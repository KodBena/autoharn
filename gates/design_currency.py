#!/usr/bin/env python3
"""design_currency — the design/FABLE-DESIGN-CURRENCY-ADVISORY-SPEC.md advisory gate.
Modeled on gates/idris_model_freshness.py (the same ADVISORY polarity: it prints `!! ADVISORY`
lines and always exits 0 at commit time; --strict is the human-facing flag that turns the same
findings into a nonzero exit for someone who wants a return code, not a wall of text).

WHAT THIS CHECKS (spec §3, five mechanical checks, none heuristic). `design/*.md` — non-
recursive, exactly the 90 docs at this file's own top level (design/workflows/ and any other
subdirectory is out of scope, same as `design/*.md`'s own glob) — may carry ONE machine-readable
currency header, an HTML comment near the top:

    <!-- design-currency: status=<token> [discharged-by=<sha>] [superseded-by=<path>]
         [depends-on=<path>[,<path>...]] -->

Free-prose `Status:` lines are NEVER parsed (spec §3 item 5) — a heuristic that guesses a
human-authored sentence's meaning manufactures exactly the false certainty this project refuses
(ADR-0000's two-biases ruling, ledger row 1887). Absence of a header is not a violation; it is
counted once, honestly, in the one back-catalog line (check 5) — the back-catalog migrates on
touch (the ADR-0017 Rule 4 precedent this spec explicitly invokes), never by sweep.

STATUS TOKENS — EIGHT, SETTLED (spec §6, amended 2026-07-27). The governing spec originally had
§2 enumerate exactly EIGHT status tokens by name (proposed, ratified, in-build, discharged,
superseded, rejected, evergreen, historical) while §6's closure statement called the set "nine" —
a self-inconsistency this module's first build flagged rather than silently resolved, implementing
the eight §2 actually named. The spec's own 2026-07-27 amendment round corrected §6 to say eight,
matching §2 — the builder's reading was right, and it is now the settled letter, not an open
question this module works around. A status token outside this set of eight remains an
unknown-token grammar finding (check 4), never guessed at.

THE FIVE CHECKS:
  1. DISCHARGE VERIFICATION. `discharged-by=<sha>`: advisory if `<sha>` is not an ancestor of this
     repo's HEAD (`git merge-base --is-ancestor`, run against THIS module's own repo root —
     `--repo-root` can redirect it, same as every sibling gate in this dir, see MODES below).
     `superseded-by=<path>`: advisory if the named doc does not exist under the design dir, or its
     OWN status is not live/historical/`discharged` (live = proposed/ratified/in-build — SETTLED,
     spec §3 item 1 amended 2026-07-27/945f9ab: `discharged` is a valid, in fact the STRONGEST,
     successor status; `rejected`/`superseded` stay invalid — see LIVE_OR_HISTORICAL's own
     comment below for the full account).
  2. DEPENDENCY DRIFT. For every doc whose OWN status is live (proposed/ratified/in-build):
     advisory per `depends-on` target whose status is `superseded` or `rejected` (both paths and
     statuses named). A `discharged` target raises NOTHING (satisfaction, spec §5). A `depends-on`
     target that does NOT EXIST gets its own advisory ("depends-on target missing", fix round on
     a7781ce — previously silent). A target that EXISTS but is headerless stays silent (documented
     asymmetry: check 5's no-per-doc-noise rule applies to an edge the same as to the doc itself).
     A target with a garbled/unknown status is caught by ITS OWN check-4 finding, not cross-
     referenced here — known, accepted imprecise attribution.
  3. STALE-CURRENCY SMELL — SETTLED (spec §3 item 3, amended 2026-07-27). Fires when the doc's
     OWN status is discharged/superseded/rejected, OR when its status is something ELSE
     (historical, most plausibly) but the doc ALREADY carries a verifiably-resolved
     `superseded-by`/`discharged-by` fact (i.e. check 1 above would find that fact GENUINE, not
     itself an advisory). This module's first build found the spec's original three-token letter
     missed its OWN motivating "live specimen" (§0's second bullet, LOGGING-DIRECTION-SURVEY-
     2026-07-27.md, seeded status=historical — a survey is a point-in-time record, never itself
     "superseded" as a document, per §2's own definition of `historical` — while ALSO carrying
     `superseded-by` naming its successor) and made the spirit call CLAUDE.md's letter-vs-spirit
     rule commands. The spec's own 2026-07-27 amendment ratified that call into §3 item 3's text
     directly: the historical-plus-resolved-fact case is now the LETTER, not a broadening this
     module carries alone.
     Once either gate above is satisfied, the check looks for a PRE-EXISTING, informal
     `<!-- doc-attest-exempt: ... Removal condition: ... -->` HTML comment (the convention
     gates/doc_attestation_presence.py's WAIVER_TOKEN already established for this codebase,
     scanned the same way — inside an HTML comment, never a bare substring match, so a doc that
     merely QUOTES the marker in prose is not itself flagged) still sitting on the document —
     advisory naming the doc, since a machine-verified resolution fact now coexists with an
     unreconciled human-authored marker.
  4. GRAMMAR. A malformed header — an unknown key, an unrecognized status token, a `discharged`
     without `discharged-by`, a `superseded` without `superseded-by`, a duplicate key, OR MORE
     THAN ONE `design-currency` HEADER IN THE SAME DOC (fix round on a7781ce: an earlier version
     silently parsed only the first header via `.search()` — an honest first header plus a stray,
     unverifiable second one parsed CLEAN, an ADR-0002 lying-signature shape; `re.finditer` now
     catches this, naming the doc, the header count, and every header's own status) — is an
     advisory naming the doc and the offending text (a refusal that teaches).
  5. BACK-CATALOG HONESTY. One line, no per-doc noise: "N of M design docs carry no currency
     header (adopt on touch)".

SCOPE, printed every run (same "never silent" convention gates/doc_attestation_presence.py's
`_print_exclusions` and ADR-0017 Rule 2(b) both use): `design/*.md` only, non-recursive. Never
edits a file, never deletes a marker (item 3 surfaces work; a human or a commissioned pass acts
on it — spec §4). No ledger integration in v1 (spec §4): the header is the doc-local cache of a
fact the ledger already records elsewhere; this gate checks the header against GIT, not the
ledger.

MODES:
    python3 gates/design_currency.py [--design-dir PATH] [--repo-root PATH] [--strict]

`--design-dir`/`--repo-root` are optional leading flags, either order, either or both — the same
device gates/doc_attestation_presence.py's `--doc-root`/`--ledger` and
gates/idris_model_freshness.py's `--idr-file`/`--lineage-dir` already establish, so a seen-red
fixture (or a caller outside this exact invocation) can redirect every path this module reads
without importing or monkeypatching it. `--strict` is the ONLY thing that changes the exit code:
without it, this module ALWAYS exits 0 (spec §3: "always exits 0 at commit time"); with it, exit
1 if any of checks 1-4 produced a finding, exit 0 if the run was fully clean (check 5's back-
catalog line is never itself a --strict-triggering finding — it is an honest count, not an
advisory about a specific document).

Exit codes: 0 always (default) / 0 clean or 1 any finding (--strict); 2 usage error (design dir
does not exist).

Registered close/lint line id: `design-currency`. Not wired into hooks/pre-commit as part of this
build (see this build's own witness report for why, and where the wiring would go if a future
commission takes it up) — hooks/ is frozen during a live session (CLAUDE.md, "Never modify
hooks/ ... while a live session runs there") and this gate is runnable standalone regardless.
Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DESIGN_DIR = REPO_ROOT / "design"

# Spec §2's eight NAMED status tokens (module docstring's "STATUS TOKENS" section: §6's closure
# statement once called this set nine before its 2026-07-27 amendment corrected it to eight).
STATUS_TOKENS = frozenset({
    "proposed", "ratified", "in-build", "discharged", "superseded",
    "rejected", "evergreen", "historical",
})
LIVE_STATUSES = frozenset({"proposed", "ratified", "in-build"})
# SETTLED (spec §3 item 1, amended 2026-07-27, commit 945f9ab): a superseded-by TARGET is valid
# at status live (proposed/ratified/in-build), historical, OR discharged — `discharged` (built
# AND merged) is the STRONGEST possible confirmation a successor is real, stronger than merely
# live, so excluding it (this module's original build) was backwards; the fix round (4cbbb8e)
# caught it against FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md turning discharged mid-build while
# LOGGING-DIRECTION-SURVEY-2026-07-27.md's superseded-by names it. `rejected` (never happened)
# and `superseded` (replaced again — the header should point at the chain's end) stay invalid.
LIVE_OR_HISTORICAL = LIVE_STATUSES | {"historical", "discharged"}
DISCHARGE_LIKE = frozenset({"discharged", "superseded", "rejected"})

ALLOWED_KEYS = ("status", "discharged-by", "superseded-by", "depends-on")

# `^` + MULTILINE: a real header sits flush-left (every seeded doc's convention) -- excludes an
# INDENTED grammar illustration (this spec's own §2 code block quotes the header syntax at 4-space
# indent) from being mistaken for a second real instance, found live authoring this fix round.
HEADER_RE = re.compile(r"^<!--\s*design-currency:(?P<body>.*?)-->", re.DOTALL | re.MULTILINE)
TOKEN_RE = re.compile(r"(status|discharged-by|superseded-by|depends-on)=(\S+)")
# Any doc-attest-exempt HTML comment naming an (unreconciled) "Removal condition:" clause — the
# same "must sit inside an HTML comment, never a bare substring" discipline
# gates/doc_attestation_presence.py's WAIVER_TOKEN already established for this codebase.
REMOVAL_MARKER_RE = re.compile(
    r"<!--(?:(?!-->).)*?doc-attest-exempt:(?:(?!-->).)*?Removal condition:(?:(?!-->).)*?-->",
    re.DOTALL,
)


class Header:
    """One doc's parsed currency header, or the record of why it couldn't be parsed cleanly.
    `issues` is non-empty exactly when the header is malformed (check 4); fields are populated
    best-effort even when malformed, so a doc with (say) an unknown status token but a perfectly
    fine depends-on list still participates in check 2 for its readable fields — a malformed
    header is a teaching advisory about the SPECIFIC bad field, not a license to discard the rest."""

    def __init__(self) -> None:
        self.present = False
        self.status: str | None = None
        self.discharged_by: str | None = None
        self.superseded_by: str | None = None
        self.depends_on: list[str] = []
        self.issues: list[str] = []
        self.raw_line: int = 0


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def parse_header(text: str) -> Header:
    """Parses the `<!-- design-currency: ... -->` comment(s) found. `.present = False` when none
    exists — NOT a grammar violation, the back-catalog case (check 5).

    MULTIPLE HEADERS (fix round on a7781ce): grammar defines exactly ONE header per doc. An
    earlier `HEADER_RE.search` (first-match-only) let a doc with an honest first header and a
    stray, unverifiable second one parse CLEAN (an ADR-0002 lying-signature shape). Now checked
    via `re.finditer`: >1 match is itself a check-4 advisory naming the doc, the count, and every
    match's own status (or `<missing>`) — never silently taking the first. The FIRST header's
    fields still populate this Header (nothing better to prefer once malformed on this axis)."""
    h = Header()
    matches = list(HEADER_RE.finditer(text))
    if not matches:
        return h
    h.present = True
    if len(matches) > 1:
        statuses = []
        for dup in matches:
            sm = re.search(r"status=(\S+)", dup.group("body"))
            statuses.append(sm.group(1) if sm else "<missing>")
        h.issues.append(f"multiple design-currency headers ({len(matches)} found, statuses "
                         f"{statuses}); only one is defined by the grammar")
    m = matches[0]
    h.raw_line = _line_of(text, m.start())
    body = m.group("body")

    seen_keys: set[str] = set()
    consumed = 0
    for tm in re.finditer(r"\S+", body):
        token = tm.group(0)
        km = TOKEN_RE.fullmatch(token)
        if not km:
            h.issues.append(f"unrecognized token {token!r} (grammar is key=value, keys "
                             f"limited to {', '.join(ALLOWED_KEYS)})")
            continue
        key, val = km.group(1), km.group(2)
        if key in seen_keys:
            h.issues.append(f"duplicate field {key!r}")
            continue
        seen_keys.add(key)
        consumed += 1
        if key == "status":
            if val not in STATUS_TOKENS:
                h.issues.append(f"unknown status token {val!r} (closed set: "
                                 f"{', '.join(sorted(STATUS_TOKENS))}) — an unrecognized token is "
                                 f"never guessed at")
            h.status = val
        elif key == "discharged-by":
            h.discharged_by = val
        elif key == "superseded-by":
            h.superseded_by = val
        elif key == "depends-on":
            h.depends_on = [p for p in val.split(",") if p]

    if h.status is None:
        h.issues.append("missing required field 'status'")
    if h.status == "discharged" and h.discharged_by is None:
        h.issues.append("status=discharged requires 'discharged-by'")
    if h.status == "superseded" and h.superseded_by is None:
        h.issues.append("status=superseded requires 'superseded-by'")
    return h


def has_removal_marker(text: str) -> bool:
    return bool(REMOVAL_MARKER_RE.search(text))


def is_ancestor(sha: str, repo_root: Path) -> bool:
    """True iff `sha` is a valid, resolvable ancestor of `repo_root`'s HEAD. Any failure mode —
    an invalid object name, a sha that exists but isn't an ancestor, no git repo at all — reads as
    False here: this check only ever needs to distinguish 'verifiably an ancestor' from
    everything else, and every 'everything else' case is the same honest advisory (spec §3 item
    1), never a crash."""
    try:
        cp = subprocess.run(
            ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", sha, "HEAD"],
            capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return cp.returncode == 0


def discover_docs(design_dir: Path) -> list[Path]:
    return sorted(design_dir.glob("*.md"))


def check_discharge_verification(rel: str, h: Header, headers: dict[str, Header],
                                  repo_root: Path) -> list[str]:
    out: list[str] = []
    if h.discharged_by is not None:
        if not is_ancestor(h.discharged_by, repo_root):
            out.append(f"{rel}: status=discharged names discharged-by={h.discharged_by}, which "
                       f"is not a verifiable ancestor of HEAD (invalid sha, or a real commit that "
                       f"is not actually merged) — the discharge claim cannot be confirmed")
    if h.superseded_by is not None:
        target_path = DESIGN_DIR / h.superseded_by
        if not target_path.exists():
            out.append(f"{rel}: status=superseded names superseded-by={h.superseded_by}, which "
                       f"does not exist under {DESIGN_DIR}")
        else:
            target_h = headers.get(h.superseded_by)
            target_status = target_h.status if target_h is not None else None
            if target_status not in LIVE_OR_HISTORICAL:
                out.append(f"{rel}: superseded-by={h.superseded_by} names a successor whose own "
                           f"status is {target_status!r}, not a live/historical/discharged token "
                           f"— a successor that was itself rejected or further superseded leaves "
                           f"{rel} un-superseded in fact")
    return out


def check_dependency_drift(rel: str, h: Header, headers: dict[str, Header]) -> list[str]:
    """Spec §3 item 2. Fix round on a7781ce: `depends-on=NoSuchDoc.md` previously read exactly
    like a healthy live dependency (target status None, not in the drift set, nothing fired) —
    gains the SAME existence check its superseded-by sibling already has, its own message
    ("depends-on target missing") so it is never confused with drift.

    ASYMMETRIC BOUNDARY, a deliberate choice: a target that EXISTS but is headerless stays SILENT
    (check 5's no-per-doc-noise rule applied to an edge — no status to have drifted FROM yet).

    KNOWN, ACCEPTED IMPRECISE ATTRIBUTION (reviewer's minor observation): a target with a garbled
    status is caught by ITS OWN check-4 finding, not a dedicated message here — imprecise
    attribution, not total silence."""
    out: list[str] = []
    if h.status not in LIVE_STATUSES:
        return out
    for dep in h.depends_on:
        target_path = DESIGN_DIR / dep
        if not target_path.exists():
            out.append(f"{rel} (status={h.status}) depends-on={dep} — depends-on target missing "
                       f"(no such doc under {DESIGN_DIR})")
            continue
        dep_h = headers.get(dep)
        dep_status = dep_h.status if dep_h is not None else None
        if dep_status in ("superseded", "rejected"):
            out.append(f"{rel} (status={h.status}) depends-on={dep} (status={dep_status}) — "
                       f"the dependency is drift, not satisfaction: {rel} leans on direction that "
                       f"has moved")
    return out


def check_stale_currency_smell(rel: str, h: Header, text: str) -> list[str]:
    """See module docstring's item-3 section for the deliberate letter-vs-spirit broadening this
    implements: fires when status is literally discharged/superseded/rejected, OR when the doc's
    own discharged-by/superseded-by fact is independently GENUINE (no advisory from check 1 for
    that same field) regardless of the chosen status token (the historical+superseded-by shape
    the spec's own live specimen uses)."""
    if not has_removal_marker(text):
        return []
    resolved = h.status in DISCHARGE_LIKE
    if not resolved and h.superseded_by is not None:
        target_path = DESIGN_DIR / h.superseded_by
        target_h = parse_header(target_path.read_text(encoding="utf-8")) if target_path.exists() else None
        resolved = target_h is not None and target_h.status in LIVE_OR_HISTORICAL
    if not resolved and h.discharged_by is not None:
        resolved = is_ancestor(h.discharged_by, REPO_ROOT)
    if not resolved:
        return []
    return [f"{rel}: status={h.status} is a resolved currency state (or names a genuinely "
            f"resolved successor/discharge) but the document still carries an unreconciled "
            f"'doc-attest-exempt ... Removal condition:' marker — the condition this marker "
            f"names is due for action (retire/rewrite the doc, or strike the marker), not left "
            f"standing silently"]


def check_grammar(rel: str, h: Header) -> list[str]:
    return [f"{rel}: line {h.raw_line}: {issue}" for issue in h.issues]


def main(argv: list[str]) -> int:
    global REPO_ROOT, DESIGN_DIR
    argv = list(argv)
    repo_root = REPO_ROOT
    while len(argv) >= 2 and argv[0] in ("--design-dir", "--repo-root"):
        flag, val = argv[0], argv[1]
        if flag == "--design-dir":
            DESIGN_DIR = Path(val).expanduser().resolve()
        else:
            repo_root = Path(val).expanduser().resolve()
        argv = argv[2:]
    strict = "--strict" in argv

    if not DESIGN_DIR.is_dir():
        print(f"design_currency: usage error — design dir does not exist: {DESIGN_DIR}",
              file=sys.stderr)
        return 2

    docs = discover_docs(DESIGN_DIR)
    headers: dict[str, Header] = {}
    texts: dict[str, str] = {}
    for p in docs:
        rel = p.name
        text = p.read_text(encoding="utf-8")
        texts[rel] = text
        headers[rel] = parse_header(text)

    findings: list[str] = []
    headerless = 0
    for p in docs:
        rel = p.name
        h = headers[rel]
        if not h.present:
            headerless += 1
            continue
        if h.issues:
            findings.extend(check_grammar(rel, h))
            continue  # a malformed header's other fields are not trustworthy enough to check
        findings.extend(check_discharge_verification(rel, h, headers, repo_root))
        findings.extend(check_dependency_drift(rel, h, headers))
        findings.extend(check_stale_currency_smell(rel, h, texts[rel]))

    if findings:
        print(f"design_currency: {len(findings)} finding(s) over {len(docs)} design doc(s):")
        for f in findings:
            print(f"  !! ADVISORY — {f}")
    else:
        print(f"design_currency: clean — {len(docs)} design doc(s) checked, 0 findings")
    print(f"design_currency: back-catalog — {headerless} of {len(docs)} design docs carry no "
          f"currency header (adopt on touch)")

    if strict:
        return 1 if findings else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
