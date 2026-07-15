#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T21:38:58Z
#   last-change: 2026-07-15T21:38:58Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""idris_model_freshness — currency gate for design/Autoharn.idr (ledger item
`idris-model-freshness-gate`). design/Autoharn.idr is CATEGORICAL DOCUMENTATION of the kernel
(its own header: "never the source of truth -- the kernel ... governs, always"). Documentation
that silently drifts behind the substrate it describes is exactly ADR-0011's "invisible-at-
authoring, visible-only-in-aggregate defect": nobody notices a stale model until a reader trusts
it. This gate makes that drift a checked property instead of a hope.

WHAT THIS CHECKS, IN TWO INDEPENDENT DIMENSIONS.

  1. DECLARED-VS-ACTUAL CHAIN HEAD. The file's own header carries a line of the form

         ||| AS-OF: kernel chain through sNN (+ ... parenthetical ...)

     naming the highest kernel/lineage delta the model claims to transcribe. The ACTUAL head is
     derived MECHANICALLY from kernel/lineage/*.sql filenames -- never hand-copied, so a future
     sNN landing cannot silently outrun this gate without it noticing (the whole point named in
     this ledger item's brief: two concurrent builders own s34/s35, and this gate must not need
     editing when their deltas land). A primary delta file matches `s<NN>-*.sql` with EXACTLY one
     dot (the `.sql` extension) in its name -- this excludes a delta's own `.detect.sql`,
     `.verify.sql`, and `.accommodate.sql` siblings (and compound siblings like
     `.accommodate.verify.sql`), which are companion probes for the SAME delta, not a later one.
     declared < actual => the model is stale:
       - RED, with teach-text naming BOTH honest discharge paths (refresh-and-bump, or an
         honest lag note), UNLESS the AS-OF line (or the text immediately following it, up to
         the next `|||` header line) carries an explicit `LAGGING: <reason>` marker -- in which
         case the finding is a loud WARN, not a failure: the model owns up to its own lag in the
         text a reader sees, so the gate does not need to lie green OR block every commit until
         someone refreshes a whole categorical model. declared >= actual is clean on this leg
         (a model is never penalized for describing a NEWER head than the mechanical scan finds,
         though that would itself be a strange state worth a human's attention).

  2. ELABORATION. `idris2 --check` on the file, regardless of AS-OF currency: a model whose
     AS-OF claims perfect currency but does not even TYPE-CHECK is a worse lie than a stale one,
     so elaboration failure is RED unconditionally -- it is checked and reported independent of
     the freshness verdict above, never short-circuited by it.

WHY declared-vs-actual is NOT a lie detector on the model's CONTENT (named honestly, not glossed
over): this gate cannot tell whether the model's prose actually transcribes the new delta's
semantics correctly -- only that it CLAIMS to (via AS-OF) and whether that claim is at least as
current as the mechanical head. A refresh that bumps AS-OF without truly updating the semantics
would pass this gate; that is a review-time defect, same class ADR-0017's doc-attestation-
presence gate names for prose review generally (checks PRESENCE+SHAPE, never CONTENT). What this
gate closes is the narrower, fully mechanizable claim: "the file does not even ASSERT currency
with what exists," which is the class that decays silently and unwitnessed.

IDRIS2 DISCOVERY: PATH is probed first (`idris2` resolved via shutil.which), falling back to the
one absolute install path this deployment is known to carry
(`/home/bork/.local/idris2/bin/idris2`) if PATH resolution fails. Neither present => exit 2
(environment error, distinct from a RED finding -- the gate cannot assess elaboration at all,
which is not the same claim as "elaboration failed").

ELABORATION MECHANICS: the target file is copied into a fresh temp directory UNDER ITS OWN
MODULE-DECLARING NAME (`Autoharn.idr`, matching `module Autoharn` inside it -- Idris refuses a
module/filename mismatch) before `--check` runs there, so the check never writes a `build/`
directory into the tracked `design/` tree and a synthetic/mutated copy (as the seen-red negative
controls use) never collides with the real file's name.

CLI (leading optional flags, either order, either or both -- the doc_attestation_presence.py
precedent this file follows for the identical reason: a caller outside this exact invocation,
or this gate's own seen-red fixtures, can redirect every path this module reads without
importing or monkeypatching it):

    python3 gates/idris_model_freshness.py
        [--idr-file PATH] [--lineage-dir PATH] [--idris2-bin PATH]

Exit codes: 0 clean or WARN-only, 1 RED (stale-without-LAGGING and/or elaboration failure),
2 usage/environment error (missing idris2, missing target file, unreadable lineage dir).

Registered close/lint line id: `idris-model-freshness`. Lazy imports are banned (CLAUDE.md,
2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
IDR_FILE = REPO_ROOT / "design" / "Autoharn.idr"
LINEAGE_DIR = REPO_ROOT / "kernel" / "lineage"
IDRIS2_FALLBACK = Path("/home/bork/.local/idris2/bin/idris2")

AS_OF_RE = re.compile(r"\|\|\|\s*AS-OF:\s*kernel chain through s(\d+)\b(?P<rest>.*)$", re.MULTILINE)
LAGGING_RE = re.compile(r"LAGGING:\s*(.+)")
DELTA_FILE_RE = re.compile(r"^s(\d+)-")


def find_idris2(explicit: str | None) -> Path | None:
    """PATH first, then the one known absolute install path. `explicit` (--idris2-bin) wins over
    both when given, so a seen-red fixture or an unusual host can redirect this deterministically."""
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    which = shutil.which("idris2")
    if which:
        return Path(which)
    if IDRIS2_FALLBACK.exists():
        return IDRIS2_FALLBACK
    return None


def parse_as_of(text: str) -> tuple[int, str | None]:
    """(declared sNN, lagging-reason-or-None) from the file's AS-OF line. Raises ValueError if no
    AS-OF line is found at all -- a model with no currency claim is not silently treated as
    infinitely fresh."""
    m = AS_OF_RE.search(text)
    if not m:
        raise ValueError("no '||| AS-OF: kernel chain through sNN' line found")
    declared = int(m.group(1))
    rest = m.group("rest") or ""
    # The LAGGING marker may sit in the same line's parenthetical, or (rare, but not refused) on
    # a continuation before the next '|||' header -- scan from the AS-OF line to the next '|||'
    # line, not just the rest of THIS line, so a wrapped note is not missed.
    tail_start = m.end()
    next_header = text.find("|||", tail_start)
    window = text[tail_start:] if next_header == -1 else text[tail_start:next_header]
    lm = LAGGING_RE.search(rest) or LAGGING_RE.search(window)
    reason = lm.group(1).strip().rstrip("*/) ").strip() if lm else None
    return declared, reason


def derive_actual_head(lineage_dir: Path) -> int:
    """The highest sNN carried by a PRIMARY delta file -- `s<NN>-*.sql` with exactly one dot (the
    `.sql` extension). `.detect.sql` / `.verify.sql` / `.accommodate.sql` (and compound siblings)
    carry >=2 dots and are excluded: they are companion probes for the delta already counted by
    its primary file, not a later delta. Files with no `sNN-` prefix (`nla-schema.sql`,
    `high_watermark_1.sql`) are not part of the numbered chain and are skipped."""
    heads = []
    for p in sorted(lineage_dir.glob("s*.sql")):
        if p.name.count(".") != 1:
            continue
        m = DELTA_FILE_RE.match(p.name)
        if m:
            heads.append(int(m.group(1)))
    if not heads:
        raise ValueError(f"no numbered sNN-*.sql delta files found under {lineage_dir}")
    return max(heads)


def run_elaboration(idr_file: Path, idris2_bin: Path) -> tuple[bool, str]:
    """True/output for `idris2 --check` on a copy of idr_file, named after its own module
    (`Autoharn.idr`) in a scratch temp dir -- never run in place (keeps `design/` free of build
    artifacts) and never under a mismatched name (Idris refuses module/filename mismatch, which
    would read as a false elaboration failure unrelated to the file's real content)."""
    with tempfile.TemporaryDirectory(prefix="idris-model-freshness-") as tmp:
        target = Path(tmp) / "Autoharn.idr"
        target.write_bytes(idr_file.read_bytes())
        cp = subprocess.run(
            [str(idris2_bin), "--check", str(target)],
            cwd=tmp, capture_output=True, text=True, timeout=120,
        )
        ok = cp.returncode == 0
        out = (cp.stdout or "") + (cp.stderr or "")
        return ok, out.strip()


def main(argv: list[str]) -> int:
    global IDR_FILE, LINEAGE_DIR
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--idr-file", default=None)
    ap.add_argument("--lineage-dir", default=None)
    ap.add_argument("--idris2-bin", default=None)
    a = ap.parse_args(argv)
    if a.idr_file:
        IDR_FILE = Path(a.idr_file).expanduser().resolve()
    if a.lineage_dir:
        LINEAGE_DIR = Path(a.lineage_dir).expanduser().resolve()

    if not IDR_FILE.exists():
        print(f"idris_model_freshness: usage error — target file does not exist: {IDR_FILE}",
              file=sys.stderr)
        return 2
    if not LINEAGE_DIR.is_dir():
        print(f"idris_model_freshness: usage error — lineage dir does not exist: {LINEAGE_DIR}",
              file=sys.stderr)
        return 2

    idris2_bin = find_idris2(a.idris2_bin)
    if idris2_bin is None:
        print("idris_model_freshness: usage error — idris2 not found on PATH and the known "
              f"fallback ({IDRIS2_FALLBACK}) does not exist. Cannot assess elaboration.",
              file=sys.stderr)
        return 2

    text = IDR_FILE.read_text(encoding="utf-8")
    try:
        declared, lagging_reason = parse_as_of(text)
    except ValueError as e:
        print(f"idris_model_freshness: RED — {IDR_FILE}: {e} (a model carrying no currency "
              f"claim at all cannot be presumed fresh)")
        return 1
    try:
        actual = derive_actual_head(LINEAGE_DIR)
    except ValueError as e:
        print(f"idris_model_freshness: usage error — {e}", file=sys.stderr)
        return 2

    findings: list[str] = []
    red = False

    if declared < actual:
        if lagging_reason:
            findings.append(
                f"WARN — {IDR_FILE.name}'s AS-OF declares kernel chain through s{declared}, but "
                f"the actual kernel/lineage/*.sql head is s{actual} (mechanically derived). The "
                f"AS-OF line honestly discloses the lag (LAGGING: {lagging_reason}) — treated as "
                f"a loud warning, not a failure. Refresh the model and drop the LAGGING suffix "
                f"when the semantics genuinely catch up.")
        else:
            findings.append(
                f"RED — {IDR_FILE.name}'s AS-OF declares kernel chain through s{declared}, but "
                f"the actual kernel/lineage/*.sql head is s{actual} (mechanically derived from "
                f"filenames, excluding .detect/.verify/.accommodate siblings). The model is "
                f"stale. Two honest discharge paths, name one: (1) REFRESH — update the model's "
                f"semantics to transcribe s{actual} and bump the AS-OF line to say so, only after "
                f"verifying the new delta's semantics are actually rendered (never bump AS-OF on "
                f"faith); or (2) LAG HONESTLY — amend the AS-OF line with an explicit "
                f"'LAGGING: <reason>' suffix, which downgrades this exact finding to a WARN "
                f"instead of a lying green. A stale, silent AS-OF claim is refused either way.")
            red = True

    ok, out = run_elaboration(IDR_FILE, idris2_bin)
    if not ok:
        findings.append(
            f"RED — idris2 elaboration of {IDR_FILE.name} FAILED (checked unconditionally, "
            f"independent of AS-OF currency):\n{out}")
        red = True

    if findings:
        print(f"idris_model_freshness: {len(findings)} finding(s) for {IDR_FILE}:")
        for f in findings:
            print(f"  !! {f}")
    else:
        print(f"idris_model_freshness: clean ✓ — {IDR_FILE.name} AS-OF (s{declared}) matches or "
              f"leads the actual lineage head (s{actual}), and idris2 --check elaborates "
              f"(zero errors).")

    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
