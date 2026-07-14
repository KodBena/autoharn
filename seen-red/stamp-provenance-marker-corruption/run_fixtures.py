#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T01:14:15Z
#   last-change: 2026-07-14T01:15:18Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for the stamp-provenance-marker-corruption fix
(tracker slug `stamp-provenance-marker-corruption`).

Witnessed defect (re-witnessed live by the compound-nominal-detection-2 builder,
2026-07-13): `hooks/stamp_provenance.py` detected an existing banner by scanning for the
marker text as a bare substring on ANY line (`BEGIN_MARK in ln`). A line that merely
MENTIONS the marker -- inside a regex literal, a doc comment describing the format, a
quoted specimen in a fixture -- was mistaken for a real banner and REPLACED, corrupting
content that never was a banner. The fix (`_find_banner` / `_looks_like_damaged_banner` in
hooks/stamp_provenance.py) requires the full fixed 5-line canonical shape at the exact
structural offsets, not a bare substring, before treating a candidate as a real banner.

Real infra, no mocks: every case below imports `hooks.stamp_provenance` directly and runs
its actual `stamp()` function against real files in a real temp directory, then reads the
files back off disk to check the result -- never a mocked filesystem, never an assertion on
an intermediate data structure the function did not actually persist (ADR-0013 Rule 5:
verify the artifact, not the claim).

The literal contiguous marker text (">>> " + "PROVENANCE-STAMP" + " >>>", etc.) is never
written into THIS file's own source, for the same reason `tools/experiments/
compound_nominal_scan2.py` assembles it from parts: this file is itself subject to the live
stamp_provenance PostToolUse hook while being authored, and a contiguous literal here would
be exactly the specimen this fixture exists to prove is now handled -- but self-testing via
self-corruption is not the point of this file, so it borrows the same split-literal idiom
and assembles the literal marker text only into the STRING CONTENT written to disk for each
case, at runtime, never into this file's own source text.

Cases:
  a-stray-mention-in-code-preserved   -- RED (pre-fix): a Python file containing a
                                         regex-literal line whose STRING VALUE is the
                                         contiguous marker text, embedded mid-line inside
                                         other code (not at column 0, not followed by the
                                         other 4 banner lines). Pre-fix, this line is
                                         mistaken for a banner and replaced/corrupted.
                                         Post-fix: the line is untouched, and a real banner
                                         is freshly inserted at the top of the file.
  b-doc-comment-mention-preserved     -- a comment line that mentions the begin-marker text
                                         as English prose ("... marker >>> PROVENANCE-STAMP
                                         >>> is ..."), not followed by real banner metadata
                                         lines. Preserved untouched; a fresh banner is
                                         inserted above it.
  c-fresh-insert-no-mention           -- baseline: a file with no marker mention anywhere
                                         gets a banner inserted after any shebang, unchanged
                                         otherwise.
  d-real-banner-updated-in-place      -- baseline: a file already carrying a REAL,
                                         structurally-complete banner has it updated in
                                         place (last-change bumped, contributor appended,
                                         first-seen preserved) -- no duplicate banner
                                         appears, no other content moves.
  e-truncated-real-banner-refused     -- a REAL banner missing its end-marker line (hand-
                                         damaged) is refused (file untouched byte-for-byte)
                                         -- the old "malformed/truncated banner" safety net,
                                         preserved by `_looks_like_damaged_banner`.
  f-marker-in-regex-among-real-code   -- NOT a red case (confirmed: passes pre-fix too) --
                                         a regression baseline for the split-literal
                                         workaround `compound_nominal_scan2.py` itself
                                         adopted to dodge this defect (`_MARK = "PROV" "
                                         ENANCE-STAMP"`; the marker built by runtime string
                                         concatenation). Because that idiom's SOURCE TEXT
                                         never contains the contiguous marker substring, it
                                         was never a specimen of the defect this fixture's
                                         (a)/(b) cases prove fixed -- it is kept here only
                                         to confirm the fix leaves that pre-existing,
                                         already-safe workaround file shape unaffected.

Usage: python3 seen-red/stamp-provenance-marker-corruption/run_fixtures.py
Exit 0 if every case matches its expected outcome; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
STAMP_MODULE_PATH = REPO / "hooks" / "stamp_provenance.py"

_spec = importlib.util.spec_from_file_location("stamp_provenance", STAMP_MODULE_PATH)
assert _spec is not None and _spec.loader is not None
stamp_provenance = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stamp_provenance)

# Assembled at runtime, matching this project's own established idiom (tools/experiments/
# compound_nominal_scan2.py) for never carrying the contiguous marker text in a file's own
# source while still being able to construct real specimen content for a fixture.
_MARK = "PROV" "ENANCE-STAMP"
_BEGIN = f">>> {_MARK} >>>"
_END = f"<<< {_MARK} <<<"

NOW = "2026-07-14T00:00:00Z"


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def main() -> int:
    failures: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="stamp-provenance-fx-"))

    try:
        # --- a: marker text embedded mid-line inside a regex literal (not at column 0) -------
        pa = tmp / "a_stray_regex.py"
        stray_line = f'STAMP_RE = re.compile(r"{_BEGIN}.*?{_END}", re.S)  # matches a banner'
        before_a = (
            "#!/usr/bin/env python3\n"
            "import re\n\n"
            f"{stray_line}\n"
            "print('hello')\n"
        )
        pa.write_text(before_a, encoding="utf-8")
        stamp_provenance.stamp(pa, "sess0001", "main", NOW)
        after_a = pa.read_text(encoding="utf-8")
        ok_a = (
            stray_line in after_a
            and "print('hello')" in after_a
            and after_a.count(_BEGIN) == 2  # the stray mention + the one real banner inserted
            and after_a.count("first-seen :") == 1
        )
        check("a-stray-mention-in-code-preserved", ok_a,
              f"stray_line_preserved={stray_line in after_a} "
              f"begin_mark_occurrences={after_a.count(_BEGIN)} "
              f"banner_count={after_a.count('first-seen :')}\n--- resulting file ---\n{after_a}",
              failures)

        # --- b: marker text as English prose inside a comment --------------------------------
        pb = tmp / "b_doc_comment.py"
        prose_line = f"# the banner marker {_BEGIN} is how a real stamp begins"
        before_b = f"{prose_line}\nvalue = 42\n"
        pb.write_text(before_b, encoding="utf-8")
        stamp_provenance.stamp(pb, "sess0001", "main", NOW)
        after_b = pb.read_text(encoding="utf-8")
        ok_b = prose_line in after_b and "value = 42" in after_b and after_b.count("first-seen :") == 1
        check("b-doc-comment-mention-preserved", ok_b,
              f"prose_line_preserved={prose_line in after_b} "
              f"banner_count={after_b.count('first-seen :')}\n--- resulting file ---\n{after_b}",
              failures)

        # --- c: baseline fresh insert, no mention at all --------------------------------------
        pc = tmp / "c_fresh.py"
        before_c = "#!/usr/bin/env python3\nprint('no marker here')\n"
        pc.write_text(before_c, encoding="utf-8")
        stamp_provenance.stamp(pc, "sess0001", "main", NOW)
        after_c = pc.read_text(encoding="utf-8")
        lines_c = after_c.split("\n")
        ok_c = (
            lines_c[0] == "#!/usr/bin/env python3"
            and _BEGIN in lines_c[1]
            and "print('no marker here')" in after_c
            and after_c.count("first-seen :") == 1
        )
        check("c-fresh-insert-no-mention", ok_c,
              f"line1={lines_c[1]!r} banner_count={after_c.count('first-seen :')}\n"
              f"--- resulting file ---\n{after_c}", failures)

        # --- d: a REAL, structurally-complete banner is updated in place ----------------------
        pd = tmp / "d_real_banner.py"
        real_block = "\n".join(stamp_provenance._build_block(
            "#", "2026-07-01T00:00:00Z", "2026-07-01T00:00:00Z", ["aaaaaaaa/main"]))
        before_d = f"#!/usr/bin/env python3\n{real_block}\n\nprint('body')\n"
        pd.write_text(before_d, encoding="utf-8")
        stamp_provenance.stamp(pd, "bbbbbbbb", "main", NOW)
        after_d = pd.read_text(encoding="utf-8")
        ok_d = (
            after_d.count("first-seen :") == 1  # updated in place, not duplicated
            and "first-seen : 2026-07-01T00:00:00Z" in after_d  # preserved
            and f"last-change: {NOW}" in after_d  # bumped
            and "aaaaaaaa/main" in after_d and "bbbbbbbb/main" in after_d  # both contributors
            and "print('body')" in after_d
        )
        check("d-real-banner-updated-in-place", ok_d,
              f"banner_count={after_d.count('first-seen :')}\n--- resulting file ---\n{after_d}",
              failures)

        # --- e: a REAL banner missing its end-marker line (hand-damaged) is refused -----------
        pe = tmp / "e_truncated.py"
        before_e = (
            f"#!/usr/bin/env python3\n"
            f"# {_BEGIN} (auto; hooks/stamp_provenance.py — do not hand-edit)\n"
            f"#   first-seen : 2026-07-01T00:00:00Z\n"
            f"#   last-change: 2026-07-01T00:00:00Z\n"
            f"#   contributors: aaaaaaaa/main\n"
            f"print('no end marker below -- hand-damaged')\n"
        )
        pe.write_text(before_e, encoding="utf-8")
        stamp_provenance.stamp(pe, "bbbbbbbb", "main", NOW)
        after_e = pe.read_text(encoding="utf-8")
        ok_e = after_e == before_e  # refused: byte-for-byte untouched
        check("e-truncated-real-banner-refused", ok_e,
              f"untouched={after_e == before_e}\n--- resulting file ---\n{after_e}", failures)

        # --- f: the exact witnessed shape -- an assembled marker inside real surrounding code -
        pf = tmp / "f_witnessed_shape.py"
        witnessed_line = (
            f'_MARK = "PROV" "ENANCE-STAMP"\n'
            f'STAMP_RE = re.compile(r">>> " + _MARK + r" >>>.*?<<< " + _MARK + r" <<<", re.S)'
        )
        before_f = (
            "#!/usr/bin/env python3\n"
            "import re\n\n"
            "# The stamp-block regex is assembled from parts on purpose.\n"
            f"{witnessed_line}\n"
            "def strip_markdown(text): return STAMP_RE.sub('', text)\n"
        )
        pf.write_text(before_f, encoding="utf-8")
        stamp_provenance.stamp(pf, "sess0001", "main", NOW)
        after_f = pf.read_text(encoding="utf-8")
        ok_f = (
            witnessed_line in after_f
            and "def strip_markdown" in after_f
            and after_f.count("first-seen :") == 1
        )
        check("f-marker-in-regex-among-real-code", ok_f,
              f"witnessed_line_preserved={witnessed_line in after_f} "
              f"banner_count={after_f.count('first-seen :')}\n--- resulting file ---\n{after_f}",
              failures)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- no polarity corrupted content that merely mentions the marker; "
          "real banners still insert and update correctly; a hand-damaged real banner is "
          "still refused untouched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
