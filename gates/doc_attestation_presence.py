#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T16:14:47Z
#   last-change: 2026-07-11T22:37:22Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""doc_attestation_presence — the commit-time enforcement floor for ADR-0017's A:B:C
fresh-context audit loop (law/adr/0017-the-zero-context-reader.md, "The fresh-context audit
loop" section and "Instance bindings"; BACKLOG "Zero-context-reader documentation discipline —
ADR-0017 DRAFT + measured enforcement" and "Two ratifications (maintainer, 2026-07-11
evening)"). The ADR designed this gate and left it UNBUILT; ratification question 1's YES
commissioned building AND arming it the same evening.

WHAT THIS CHECKS, AND WHAT IT DELIBERATELY DOES NOT CHECK. Every changed maintainer-facing
`*.md` file must carry a **fresh-context attestation record** in the append-only ledger
`attestations/doc-legibility-attestations.jsonl` (ATTESTATION RECORD FORMAT below) whose
`content_sha256` matches the file's CURRENT on-disk bytes. The gate verifies two things and
two things only:

  1. PRESENCE — a record exists for this exact content (by hash). No record for the content
     currently being committed means no fresh-context read has happened FOR THAT CONTENT —
     an earlier attestation of a since-edited version does not carry forward.
  2. SHAPE — the record has the structure ADR-0017's "B's verdict has a required shape, or it
     is no verdict" rule demands: a DEFECT round carries per-finding `file`/`line`/`quote`/
     `repair`; a CLEAN round enumerates all four Rule-1 clauses; the round count is within the
     ADR's two-round cap; a still-DEFECT final round is marked `escalated: true` (the
     non-converging-review-loop typed event, not a silent third round). Under doc-attestation/2
     the shape additionally binds the escalation recipient's `adjudication` (SCHEMA VERSIONS
     below): required-and-well-shaped when `escalated: true`, forbidden otherwise.

It NEVER reads what B concluded to decide pass/fail — a DEFECT-with-escalated-true record is
just as "present and well-shaped" as a CLEAN one, and the gate is satisfied by either. This is
the ratified sub-question's answer mechanized literally: "no LLM verdict blocks anything"
(BACKLOG "Two ratifications", ratification 1's sub-question 2). What blocks is the absence of
evidence that a fresh-context read happened at all, and evidence in the wrong shape (a bare
"looks compliant" is foreclosed by construction: the JSON schema has no field for one).

ATTESTATION RECORD FORMAT (one JSON object per line in the ledger; append-only, git-tracked —
this repo carries no world ledger of its own, so the record lives in-repo per ADR-0017's
instance-bindings note that a wired kernel world COULD ride countersign_obligation/review_gap,
but this repo is not that world; see the module docstring's "SMALLEST SOUND THING" note below
for what was chosen where the ADR is silent):

    {
      "schema": "doc-attestation/1",
      "doc": "design/ABC-AUDIT-LOOP-RECIPE.md",   // repo-relative path, POSIX separators
      "content_sha256": "<64-hex, sha256 of the exact bytes B read>",
      "b_id": "<free text identifying B's invocation, distinct from A's>",
      "rounds": [
        {"round": 1, "verdict": "DEFECT", "findings": [
            {"file": "design/ABC-AUDIT-LOOP-RECIPE.md", "line": 42,
             "quote": "<verbatim excerpt>", "repair": "<one-sentence fix>"}
        ], "clauses_checked": []},
        {"round": 2, "verdict": "CLEAN", "findings": [],
         "clauses_checked": ["1a", "1b", "1c", "1d"]}
      ],
      "escalated": false,
      "attested_at": "2026-07-11T21:00:00Z"
    }

`content_sha256` is what makes this an artifact-shaped check, not an identity check: ADR-0017
says plainly "the enforced surface is the attestation, not the agent's identity" and names WHY
— "identity enumeration fails open, and this project has already witnessed its write
interceptors evaded." `b_id` is a self-declared free-text field the gate requires be non-empty
but does NOT verify (no sound mechanical test separates a genuinely fresh fork from a claimed
one, same reasoning ADR-0017 gives for declining coinage-detection in Rule 2). Distinctness is
asserted in the record and reviewed like any other claim, never policed here.

SCHEMA VERSIONS — doc-attestation/1 and /2 (the full rationale is design/SPEC-DOC-ATTESTATION-2.md).
The gate accepts BOTH; an unknown `schema` string is refused (fail-closed — a version whose rules
this gate does not know cannot be shape-checked). The evolution closes ONE seam the first live
escalations exposed (BACKLOG "First live enforcement of ADR-0017's loop"): when a loop escalated,
"who adjudicated it, what they applied, and when" had no field and was written into `b_id` free
text. /2 gives it a first-class home:

    {
      "schema": "doc-attestation/2",
      ... every /1 field unchanged (doc, content_sha256, b_id, rounds, attested_at) ...
      "escalated": true,
      "adjudication": {
        "adjudicated_by": "<the escalation recipient — e.g. 'orchestrator (Fable)'>",
        "disposition":    "<what was applied — e.g. 'applied B round-2 repairs verbatim, no content change'>",
        "adjudicated_at": "<ISO-8601 timestamp of the adjudication>"
      }
    }

The invariant is typed, so both illegal shapes are refused for an honest /2 record (ADR-0000
Rule 1): a /2 record with `escalated: true` MUST carry a well-shaped `adjudication` (EXACTLY the
three fields, each a non-empty string — extra keys are refused so the object cannot itself become a
second overload home), and a /2 record with `escalated: false` MUST NOT carry one (a converged
loop had no escalation to adjudicate — an adjudication with nothing escalated is a lying record,
ADR-0002/ADR-0012 P8). Like every other field here this binds HONEST records: a record that lies
about its `schema`/`escalated` to dodge is the same evasion class as a fabricated CLEAN verdict,
which ADR-0017 never promised to catch (identity/authorship is not policed) — no shape-check closes
it, so the claim is scoped to honest records, not asserted as adversarially unrepresentable.
`adjudication` is self-declared free text the gate checks for PRESENCE and SHAPE only, never for
whether the disposition was RIGHT — identical posture to `b_id` and to B's own verdict.

MIGRATION, honestly (ADR-0017 Exceptions; ADR-0013): the ~20 existing /1 records are valid history
and are NEVER rewritten — they remain point-in-time records of loops that ran under /1, and the
gate validates them under /1's rules unchanged. New records are written at /2 (`--record` emits
it); a new escalated loop records its adjudication in the typed field instead of b_id prose. There
is no back-sweep and no /1-to-/2 rewrite: a /1 record is not "wrong", it is older.

SMALLEST SOUND THING, where the ADR is silent (named per this commission's own instruction):
  - The ledger is ONE shared append-only JSONL file, not one sidecar file per document, to
    match this repo's existing append-only-ledger convention (BACKLOG.md, the journal files
    hooks/demurral_detect.py and hooks/doc_legibility_critic.py already write) rather than
    inventing a new one.
  - Records are looked up by (doc path, content hash) pair, latest-appended match wins — so a
    document can accumulate a full attestation history across edits, and only the CURRENT
    content's record is checked at commit time (an attestation of a superseded version is
    just history, not a pass).
  - `--record` is provided as the one sanctioned way to WRITE a record (reads the doc's
    current bytes itself and computes the hash, rather than trusting a caller-supplied one) —
    a malformed record is refused at write time, not discovered at commit time.

SCOPE AND EXCLUSIONS (every one printed by every run — ADR-0017 Rule 2(b)'s printed-exclusion
convention, "never silent"):
  - Only git-tracked `*.md` files are in scope (gate mode: the files named on the command
    line; report mode: every tracked `*.md`, mirroring gates/doc_shapes.py's two-mode split).
  - BACKLOG.md is excluded WHOLESALE — ADR-0017's own Exceptions name "dated BACKLOG entries"
    as point-in-time records; the whole file changes shape on every append, and requiring a
    fresh attestation of the entire growing file on every entry would attest noise, not the
    entry (BACKLOG "Zero-context-reader documentation discipline" packet, "point-in-time
    records like BACKLOG appends").
  - `judgment/**` is excluded WHOLESALE — OPERATING-CARD.md's own words, "predecessor era —
    history unless a current spec cites it"; the same declared-history status
    gates/link_integrity.py already excludes this tree for (Rule 2(b)'s sibling gate).
  - A file carrying the HTML comment `<!-- doc-attest-exempt: <reason> -->` anywhere is
    excluded WHOLESALE, reason named inline by the author — the escape hatch for a
    point-in-time record or a quoted-defect specimen this gate's two named exclusions do not
    already cover (ADR-0017's Exceptions: point-in-time records and quoted defects), following
    gates/doc_shapes.py's `doc-shapes-allow:` waiver precedent, with one deliberate tightening:
    the token must sit inside an HTML comment, not a bare substring match — a plain substring
    check was tried first and caught itself live (this gate's own recipe doc, design/
    ABC-AUDIT-LOOP-RECIPE.md, explains the waiver token in prose as a worked example, and that
    explanation alone tripped a false exemption before the HTML-comment requirement was added).
    A waiver is a claim reviewed like any other,
    named inline rather than silent.

MODES (mirrors gates/doc_shapes.py exactly, the discipline's own binds-on-touch design):
  - `python3 gates/doc_attestation_presence.py FILE [FILE...]` — GATE mode, the touched set at
    commit time: exit 1 listing every doc with no matching or malformed record, exit 0 clean.
    This is the ONLY blocking mode.
  - `python3 gates/doc_attestation_presence.py` — REPORT mode, repo-wide: prints standing gaps,
    ALWAYS exits 0 — the back-catalog migrates on touch (ADR-0017 Rule 4), never by sweep.
  - `python3 gates/doc_attestation_presence.py --record FILE.json` — write a new record: reads
    a JSON body from FILE (or stdin if FILE is "-") carrying `doc`, `b_id`, `rounds`,
    `escalated`, an optional `attested_at` (filled with now() if absent), and — for an escalated
    loop under doc-attestation/2 — the `adjudication` object (SCHEMA VERSIONS above); computes
    `content_sha256` itself from the CURRENT bytes of `doc`; writes at `schema` = doc-attestation/2;
    validates the shape; appends one line to the ledger. Exit 0 on a valid append, exit 2 on a
    malformed input (nothing is ever appended to the ledger unvalidated) — so an escalated record
    missing its adjudication, or a non-escalated one carrying one, is refused HERE, not at commit.

ARMING MODE — ANSWERED FROM THE ADR TEXT, NOT ASSUMED (this commission's Critical Arming
Question). ADR-0017's "fresh-context audit loop" section states the attestation-presence
gate's enforcement surface in these exact words: "deterministic and **commit-time-blockable**
once built." Revisit-when #2 states this gate is the ONE exception to the tenet's own
unmeasured-promotion bar: "The attestation-presence gate (deterministic, checks that a fresh
read happened, not what it concluded) is exempt from this bar and may be built and armed on
the packet's word" — and the packet's word (BACKLOG "Two ratifications") already said YES.
Unlike hooks/doc_legibility_critic.py (a COSTED LLM call, apparatus.json-switched, default OFF
per the "no world silently bills its operator" mandate), this gate spends nothing — it is a
hash lookup and a JSON shape check, the same free-per-commit class as gates/doc_shapes.py and
gates/link_integrity.py, NEITHER of which carries an apparatus.json off-switch. So: this gate
is authored ENFORCE (gate mode exits 1 on a missing/malformed record) with no observe/off
mode and no switchboard entry — there is nothing here whose cost an operator needs to opt into.
What is DEFERRED is not the gate's own mode but its WIRING into hooks/pre-commit: this
commission's constraints forbid editing hooks/ existing files while a governed session
(run10) is live, so the pre-commit stanza is prepared and printed here rather than applied —
see the module's bottom docstring block. (A pre-existing, unrelated gap noticed in passing:
gates/doc_shapes.py, though built, seen-red, and registered days before this pass, is ALSO not
yet invoked from hooks/pre-commit's body despite the header comment's "FINAL WIRING" note
listing gates through link_integrity — flagged here per CLAUDE.md's hazard-flagging duty, not
fixed, since it is the same frozen file.)

WIRING STANZA — for the orchestrator to drop into hooks/pre-commit once the freeze lifts
(mirrors the link_integrity block immediately above it in that file):

    # doc-attestation-presence — every touched maintainer-facing *.md must carry a
    # fresh-context (A:B:C) attestation record for its exact content (ADR-0017, "The
    # fresh-context audit loop"; ratified 2026-07-11). Checks PRESENCE+SHAPE only, never the
    # attestation's conclusions — nothing here blocks on LLM judgment.
    TOUCHED_MD=$(git diff --cached --name-only --diff-filter=ACMR -- '*.md')
    if [ -n "$TOUCHED_MD" ]; then
        # shellcheck disable=SC2086
        "$PY" "$REPO_ROOT/gates/doc_attestation_presence.py" $TOUCHED_MD || {
            echo "" >&2
            echo "pre-commit: doc-attestation-presence FAILED — a changed doc carries no" >&2
            echo "fresh-context attestation record for its current content (ADR-0017)." >&2
            exit 1
        }
    fi

Exit codes: 0 clean (gate) / always (report), 1 gate-mode violations, 2 usage/IO/record error.
Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = REPO_ROOT / "attestations" / "doc-legibility-attestations.jsonl"

# Wholesale file/dir exclusions — printed every run, never silent (see module docstring).
EXCLUDE_FILES_WHOLESALE = {"BACKLOG.md"}
EXCLUDE_DIR_PREFIXES = ("judgment/",)
WAIVER_TOKEN = "doc-attest-exempt:"

RULE1_CLAUSES = {"1a", "1b", "1c", "1d"}
MAX_ROUNDS = 2  # ADR-0017's two-round B->C cap before the non-converging-review-loop escalation.

# doc-attestation SCHEMA VERSIONS (design/SPEC-DOC-ATTESTATION-2.md). /2 adds a first-class
# `adjudication` object for escalated records, replacing the b_id free-text convention the seam
# (BACKLOG "First live enforcement of ADR-0017's loop") named. /1 records stay valid history,
# unchanged and never rewritten; the gate accepts BOTH versions. --record writes SCHEMA_LATEST.
SCHEMA_V1 = "doc-attestation/1"
SCHEMA_V2 = "doc-attestation/2"
SCHEMA_LATEST = SCHEMA_V2
KNOWN_SCHEMAS = {SCHEMA_V1, SCHEMA_V2}
# The escalation recipient's disposition, /2 only: who adjudicated, what was applied, when.
ADJUDICATION_FIELDS = ("adjudicated_by", "disposition", "adjudicated_at")


def _tracked_md() -> list[str]:
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-files", "*.md"],
                        capture_output=True, text=True, check=True)
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def in_scope(rel: str) -> bool:
    if rel in EXCLUDE_FILES_WHOLESALE:
        return False
    if any(rel.startswith(p) for p in EXCLUDE_DIR_PREFIXES):
        return False
    return True


_WAIVER_COMMENT = re.compile(r"<!--\s*" + re.escape(WAIVER_TOKEN) + r".*?-->", re.DOTALL)


def _has_waiver(path: Path) -> bool:
    """A waiver requires the token inside an HTML comment (`<!-- doc-attest-exempt: reason
    -->`), never a bare substring match. A raw substring check was tried first and caught
    itself live: this gate's own recipe doc (design/ABC-AUDIT-LOOP-RECIPE.md) explains the
    waiver token in prose as a worked example, and that explanation alone tripped a false
    wholesale exemption under a plain 'WAIVER_TOKEN in text' check. Requiring the HTML-comment
    wrapper is the same device gates/link_integrity.py's strip_inline_code / strip_fences use
    to keep an example from being mistaken for the real thing."""
    try:
        return bool(_WAIVER_COMMENT.search(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeDecodeError):
        return False


# ---------------------------------------------------------------------------------------
# Ledger I/O
# ---------------------------------------------------------------------------------------

def load_ledger() -> list[dict]:
    """Every well-formed JSON line in the ledger, in file order. A malformed line is reported
    (never silently dropped) as a synthetic record carrying '_parse_error' so lookups treat it
    as absent rather than crash the gate on a corrupt ledger."""
    if not LEDGER_PATH.exists():
        return []
    records: list[dict] = []
    for i, line in enumerate(LEDGER_PATH.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            records.append({"_parse_error": f"ledger line {i}: {e}"})
            continue
        if isinstance(rec, dict):
            records.append(rec)
        else:
            records.append({"_parse_error": f"ledger line {i}: not a JSON object"})
    return records


def latest_record_for(records: list[dict], doc_rel: str, content_sha256: str) -> dict | None:
    """The latest-appended record matching this exact (doc, content-hash) pair — an
    attestation of a since-superseded version of the same file does not carry forward."""
    match = None
    for rec in records:
        if rec.get("doc") == doc_rel and rec.get("content_sha256") == content_sha256:
            match = rec
    return match


# ---------------------------------------------------------------------------------------
# Shape validation — structural only, never a judgment on B's content (see module docstring).
# ---------------------------------------------------------------------------------------

def _validate_finding(f: Any, where: str) -> list[str]:
    if not isinstance(f, dict):
        return [f"{where}: finding is not an object"]
    issues = []
    for key in ("file", "line", "quote", "repair"):
        if key not in f:
            issues.append(f"{where}: finding missing '{key}'")
    if "file" in f and (not isinstance(f["file"], str) or not f["file"].strip()):
        issues.append(f"{where}: finding 'file' is not a non-empty string")
    if "line" in f and not isinstance(f["line"], int):
        issues.append(f"{where}: finding 'line' is not an integer (needs a real file:line specimen)")
    for key in ("quote", "repair"):
        if key in f and (not isinstance(f[key], str) or not f[key].strip()):
            issues.append(f"{where}: finding '{key}' is not a non-empty string")
    return issues


def _validate_round(rnd: Any, idx: int) -> list[str]:
    where = f"rounds[{idx}]"
    if not isinstance(rnd, dict):
        return [f"{where}: not an object"]
    issues = []
    if rnd.get("round") != idx + 1:
        issues.append(f"{where}: 'round' must be {idx + 1} (rounds are sequential from 1)")
    verdict = rnd.get("verdict")
    if verdict not in ("CLEAN", "DEFECT"):
        issues.append(f"{where}: 'verdict' must be CLEAN or DEFECT, got {verdict!r}")
        return issues  # nothing further to check without a valid verdict
    findings = rnd.get("findings")
    if verdict == "DEFECT":
        if not isinstance(findings, list) or not findings:
            issues.append(f"{where}: DEFECT verdict carries no findings — an umbrella verdict "
                           f"is no verdict (ADR-0017, 'B's verdict has a required shape')")
        else:
            for j, f in enumerate(findings):
                issues.extend(_validate_finding(f, f"{where}.findings[{j}]"))
    else:  # CLEAN
        clauses = rnd.get("clauses_checked")
        # Build the set only from hashable string entries — a caller-supplied list with unhashable
        # elements ([["1a"]], [{"1a": true}]) must clean-REFUSE (the four clauses are then not all
        # present), never crash set() with a TypeError.
        if not isinstance(clauses, list) or not RULE1_CLAUSES.issubset(
                {c for c in clauses if isinstance(c, str)}):
            issues.append(f"{where}: CLEAN verdict must enumerate all four Rule 1 clauses "
                           f"(1a,1b,1c,1d) in 'clauses_checked', got {clauses!r}")
    return issues


def _validate_adjudication(adj: Any, escalated: bool) -> list[str]:
    """doc-attestation/2 only (design/SPEC-DOC-ATTESTATION-2.md). Structural, never a judgment on
    whether the adjudication was RIGHT — same posture as the rest of the gate. Two typed states,
    and the two illegal ones this field exists to make unrepresentable (ADR-0000 Rule 1):

      escalated=true  -> `adjudication` is REQUIRED and carries three non-empty strings
                         (adjudicated_by / disposition / adjudicated_at). Its absence is the seam
                         closed: an escalated record with no first-class adjudication is refused,
                         where /1 let it hide in b_id free text.
      escalated=false -> `adjudication` is FORBIDDEN. A loop that converged CLEAN had no escalation
                         recipient to adjudicate, so an adjudication with nothing escalated is a
                         lying record (ADR-0002 / ADR-0012 P8), refused here.
    """
    if escalated:
        if adj is None:
            return ["escalated record carries no 'adjudication' object — doc-attestation/2 requires "
                    "the escalation recipient's disposition (adjudicated_by / disposition / "
                    "adjudicated_at) as a first-class field, not b_id free text "
                    "(design/SPEC-DOC-ATTESTATION-2.md; the seam BACKLOG 'First live enforcement')"]
        if not isinstance(adj, dict):
            return ["'adjudication' is not an object"]
        issues = []
        for key in ADJUDICATION_FIELDS:
            if key not in adj:
                issues.append(f"'adjudication' missing '{key}'")
            elif not isinstance(adj[key], str) or not adj[key].strip():
                issues.append(f"'adjudication.{key}' is not a non-empty string")
        # The object is EXACTLY the three fields — extra keys are refused so `adjudication` cannot
        # itself become a second free-text overload home, the very defect /2 exists to end
        # (design/SPEC-DOC-ATTESTATION-2.md, closure statement).
        unknown = sorted(k for k in adj if k not in ADJUDICATION_FIELDS)
        if unknown:
            issues.append(f"'adjudication' has unexpected field(s) {unknown} — the object is exactly "
                          f"{list(ADJUDICATION_FIELDS)}, no more")
        return issues
    if adj is not None:
        return ["'adjudication' present on a non-escalated record — an adjudication with nothing "
                "escalated is unrepresentable (ADR-0000): a loop that converged CLEAN had no "
                "escalation recipient to adjudicate. Drop the field, or set escalated=true if the "
                "loop genuinely did not converge"]
    return []


def validate_record(rec: dict) -> list[str]:
    """Structural issues only — never a check on whether B's judgment was RIGHT. Empty list
    means the record is well-shaped (regardless of whether its content says CLEAN or DEFECT).
    Dispatches on `schema`: /1 rules are unchanged; /2 additionally binds the adjudication field
    (design/SPEC-DOC-ATTESTATION-2.md)."""
    if "_parse_error" in rec:
        return [rec["_parse_error"]]
    issues: list[str] = []
    for key in ("schema", "doc", "content_sha256", "b_id", "rounds", "escalated", "attested_at"):
        if key not in rec:
            issues.append(f"record missing required field '{key}'")
    if issues:
        return issues  # a record missing top-level fields isn't worth field-by-field checking
    if not isinstance(rec["schema"], str) or rec["schema"] not in KNOWN_SCHEMAS:
        # isinstance guard first: a non-string schema (a JSON list/dict) must clean-REFUSE, never
        # crash `x in set` with an unhashable-type TypeError.
        return [f"unknown schema {rec['schema']!r} — this gate validates only "
                f"{sorted(KNOWN_SCHEMAS)}; an unrecognized version cannot be shape-checked, so it "
                f"is refused (fail-closed, not fail-open)"]
    if not isinstance(rec["b_id"], str) or not rec["b_id"].strip():
        issues.append("'b_id' must be a non-empty string identifying B's invocation")
    if not re.fullmatch(r"[0-9a-f]{64}", str(rec["content_sha256"])):
        issues.append("'content_sha256' is not a 64-hex sha256 digest")
    rounds = rec["rounds"]
    if not isinstance(rounds, list) or not (1 <= len(rounds) <= MAX_ROUNDS):
        issues.append(f"'rounds' must be a list of 1..{MAX_ROUNDS} entries (ADR-0017's two-round "
                       f"B->C cap) — got {len(rounds) if isinstance(rounds, list) else type(rounds).__name__}")
        return issues
    for i, rnd in enumerate(rounds):
        issues.extend(_validate_round(rnd, i))
    if issues:
        return issues
    final_verdict = rounds[-1]["verdict"]
    escalated = rec["escalated"]
    if not isinstance(escalated, bool):
        issues.append("'escalated' must be a boolean")
    elif final_verdict == "DEFECT" and len(rounds) >= MAX_ROUNDS and not escalated:
        issues.append(f"final round is still DEFECT after {MAX_ROUNDS} rounds but 'escalated' "
                       f"is false — ADR-0017: 'B↔C non-convergence is a typed event, not a "
                       f"loop' (route it as the non-converging-review-loop escalation, don't "
                       f"grind a third round)")
    if rec["schema"] == SCHEMA_V2 and isinstance(escalated, bool):
        issues.extend(_validate_adjudication(rec.get("adjudication"), escalated))
    return issues


# ---------------------------------------------------------------------------------------
# Gate / report
# ---------------------------------------------------------------------------------------

def check_file(rel: str, records: list[dict]) -> list[str]:
    path = REPO_ROOT / rel
    if not path.exists():
        return [f"{rel}: IO file does not exist"]
    if _has_waiver(path):
        return []  # printed as excluded-by-waiver at the call site, not a violation
    content_sha256 = _sha256_of(path)
    rec = latest_record_for(records, rel, content_sha256)
    if rec is None:
        return [f"{rel}: NO-ATTESTATION no fresh-context attestation record in "
                f"attestations/doc-legibility-attestations.jsonl matches this file's current "
                f"content (sha256 {content_sha256[:12]}...) — run the A:B:C loop "
                f"(design/ABC-AUDIT-LOOP-RECIPE.md) and record it with "
                f"'gates/doc_attestation_presence.py --record', or waive with "
                f"'<!-- {WAIVER_TOKEN} <reason> -->' if this is a point-in-time record or "
                f"quoted-defect specimen the wholesale exclusions do not already cover"]
    issues = validate_record(rec)
    return [f"{rel}: MALFORMED-RECORD {issue}" for issue in issues]


def _print_exclusions(scope: list[str], excluded: list[str], waived: list[str]) -> None:
    print(f"doc_attestation_presence: {len(scope)} doc(s) in scope, {len(excluded)} excluded, "
          f"{len(waived)} waived.")
    print("  excluded (principled, printed per ADR-0017 Rule 2(b) convention):")
    print("    BACKLOG.md  — point-in-time dated entries (ADR-0017 Exceptions)")
    print("    judgment/** — declared history (OPERATING-CARD.md), same status "
          "gates/link_integrity.py already grants it")
    if waived:
        print(f"  waived by inline '<!-- {WAIVER_TOKEN} ... -->' marker:")
        for w in waived:
            print(f"    {w}")


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--record":
        return _cmd_record(argv[1:])

    gate_mode = bool(argv)
    if gate_mode:
        targets = []
        for a in argv:
            p = Path(a)
            if not p.is_absolute():
                p = REPO_ROOT / p
            if p.suffix != ".md":
                continue  # non-markdown paths pass through silently (mixed commit sets)
            if not p.exists():
                print(f"doc_attestation_presence: named file does not exist: {a}", file=sys.stderr)
                return 2
            targets.append(_rel(p))
    else:
        targets = _tracked_md()

    scope = [t for t in targets if in_scope(t)]
    excluded = [t for t in targets if not in_scope(t)]
    waived = [t for t in scope if _has_waiver(REPO_ROOT / t)]

    records = load_ledger()
    all_violations: list[str] = []
    for rel in scope:
        all_violations.extend(check_file(rel, records))

    mode_word = "gate" if gate_mode else "report"
    _print_exclusions(scope, excluded, waived)
    if all_violations:
        print(f"doc_attestation_presence ({mode_word} mode): {len(all_violations)} finding(s):")
        for v in all_violations:
            print(f"  {v}")
        if not gate_mode:
            print("doc_attestation_presence: report mode never fails — the back-catalog "
                  "migrates on touch (ADR-0017 Rule 4), not by sweep")
        return 1 if gate_mode else 0
    print(f"doc_attestation_presence ({mode_word} mode): clean — {len(scope)} doc(s) in scope, "
          f"0 findings")
    return 0


def _cmd_record(argv: list[str]) -> int:
    if not argv:
        print("usage: doc_attestation_presence.py --record FILE.json  (or '-' for stdin)",
              file=sys.stderr)
        return 2
    src = argv[0]
    try:
        raw = sys.stdin.read() if src == "-" else Path(src).read_text(encoding="utf-8")
        body = json.loads(raw)
    except (OSError, json.JSONDecodeError) as e:
        print(f"doc_attestation_presence --record: could not read/parse {src}: {e}", file=sys.stderr)
        return 2
    if not isinstance(body, dict):
        print("doc_attestation_presence --record: input must be a JSON object", file=sys.stderr)
        return 2
    doc = body.get("doc")
    if not isinstance(doc, str) or not doc:
        print("doc_attestation_presence --record: input must name 'doc' (repo-relative path)",
              file=sys.stderr)
        return 2
    doc_path = REPO_ROOT / doc
    if not doc_path.exists():
        print(f"doc_attestation_presence --record: 'doc' does not exist on disk: {doc}",
              file=sys.stderr)
        return 2
    record = {
        "schema": SCHEMA_LATEST,  # new records are written at the latest version (doc-attestation/2)
        "doc": doc,
        "content_sha256": _sha256_of(doc_path),  # computed here, never trusted from input
        "b_id": body.get("b_id"),
        "rounds": body.get("rounds"),
        "escalated": body.get("escalated"),
        "attested_at": body.get("attested_at") or time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z",
    }
    # /2 adjudication: carried through only when supplied. validate_record enforces the
    # escalated<->adjudication invariant below, so an escalated record with no adjudication (or a
    # non-escalated one carrying one) is REFUSED at write time, never appended.
    if "adjudication" in body:
        record["adjudication"] = body["adjudication"]
    issues = validate_record(record)
    if issues:
        print(f"doc_attestation_presence --record: REFUSED — malformed record for {doc}:",
              file=sys.stderr)
        for issue in issues:
            print(f"  {issue}", file=sys.stderr)
        return 2
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"doc_attestation_presence --record: appended attestation for {doc} "
          f"(schema {record['schema']}, content_sha256 {record['content_sha256'][:12]}..., "
          f"{len(record['rounds'])} round(s), escalated={record['escalated']}"
          f"{', adjudicated' if 'adjudication' in record else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
