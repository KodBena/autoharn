#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T01:26:54Z
#   last-change: 2026-07-15T01:26:54Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for panel/backend/disposition.py's two pure functions
(`derive_status`, `group_item_rows`) and panel/backend/ledger_read.py's `parse_item_refs`
(BUILD SPEC v2 r5 sec 3/5/8/10, WP-4 package).

Pure Python, NO DATABASE -- these three functions take/return plain values (dataclasses, tuples,
dicts, strings) with no SQL, no connection, no subprocess; they are the "trivially unit-testable
with no database" claim disposition.py's own module docstring makes, and this fixture is that
claim's proof. `parse_item_refs` lives in `ledger_read.py` rather than `disposition.py` (spec sec
8), but it too is pure -- a regex match over a string, nothing else -- so it belongs in this
no-DB fixture rather than panel-cosign's live-schema one.

Both-polarity: (a)/(b)/(c)/(f) are RED-shaped (each proves a case the derivation must NOT
misclassify -- the value it must NOT read as OPEN, WITNESSED, or the wrong parse -- exercised
here as an assertion that would raise AssertionError, i.e. FAIL LOUD, if the pure function ever
regressed to the wrong answer); (d)/(e)/(g)/(h)/(i)/(j) are GREEN-shaped (the correct value for a
case that must classify positively). "RED" here follows this repository's seen-red idiom loosely
-- for a pure derivation with no live infra to break, RED means "the specimen this fixture would
catch failing if the function regressed," not a live infrastructure failure; `red.txt` (banked
alongside this file, fixture_census.py's own requirement) records this fixture's own output the
one time every case was run against the as-shipped functions, so a later regression has a
banked-good baseline to diff against.

Cases (spec sec 10, exact values, including the r4/round-3 case (j) proving the anchored parser
distinguishes a prefix-adjacent item-id pair -- the single shared function BOTH the read path
(`decomposition_items`) and the write path (WP-3's seed script) now call for "does this refs
string carry item <iid>", so this one case covers the read/write divergence class end to end):

  a  derive_status(False, [])                                            -> OPEN
  b  derive_status(False, [two substantive, neither cosigned])           -> WITNESSED
  c  parse_item_refs(no panel-item token, 680)                          -> (None, [])
  f  group_item_rows((("A1",812),("A1",815)))                           -> {"A1": (812, 815)}
  d  derive_status(True, [])                                            -> COSIGNED (fast path)
  e  parse_item_refs("panel-item:680:A1 row:681 work:kr-titration-design-exploration", 680)
                                                                          -> ("A1", [...])
  g  derive_status(False, [one cosigned, one not])                      -> PARTIAL
  h  derive_status(False, [both cosigned])                              -> COSIGNED (equivalence)
  i  group_item_rows((("A1",812),("A2",900)))                           -> {"A1": (812,), "A2": (900,)}
  j  parse_item_refs("panel-item:680:A10 row:900", 680) -> item_id == "A10" AND item_id != "A1"

Usage: python3 seen-red/panel-disposition/run_fixtures.py
Exit 0 if every case matches; 1 otherwise, listing every mismatch. Lazy imports banned.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "panel" / "backend"))  # config.py, disposition.py, ledger_read.py
                                                       # are flat sibling imports internally --
                                                       # see panel/backend/ledger_read.py's own
                                                       # "import config" / "from disposition
                                                       # import ..." -- so this fixture reaches
                                                       # them the same way panel/seed/
                                                       # author_0714_decomposition.py does.

from disposition import WitnessFacts, derive_status, group_item_rows  # noqa: E402
from ledger_read import parse_item_refs  # noqa: E402


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def main() -> int:
    failures: list[str] = []

    # --- a: no witnesses, item row not cosigned -> OPEN ------------------------------------------
    ra = derive_status(False, [])
    check("a-open-no-witnesses", ra == "OPEN", f"derive_status(False, []) = {ra!r} (want OPEN)", failures)

    # --- b: two substantive witnesses, neither individually cosigned -> WITNESSED ----------------
    rb = derive_status(False, [
        WitnessFacts("row", "681", True, True, 681, False),
        WitnessFacts("row", "716", True, True, 716, False),
    ])
    check("b-witnessed-none-cosigned", rb == "WITNESSED",
          f"derive_status(False, [two substantive, neither cosigned]) = {rb!r} (want WITNESSED)", failures)

    # --- c: no panel-item token at all -> fail-closed (None, []) ----------------------------------
    rc = parse_item_refs("row:1 work:foo", 680)
    check("c-no-item-token-fail-closed", rc == (None, []),
          f"parse_item_refs('row:1 work:foo', 680) = {rc!r} (want (None, []))", failures)

    # --- f: two independent rows claim the SAME item id -> the collision is CARRIED, not narrowed
    rf = group_item_rows((("A1", 812), ("A1", 815)))
    check("f-collision-carried", rf == {"A1": (812, 815)},
          f"group_item_rows(((A1,812),(A1,815))) = {rf!r} (want {{'A1': (812, 815)}})", failures)

    print("---- RED cases above; GREEN cases below ----\n")

    # --- d: item row's OWN cosign wins even with zero witnesses (the fast path) -------------------
    rd = derive_status(True, [])
    check("d-item-row-fast-path", rd == "COSIGNED",
          f"derive_status(True, []) = {rd!r} (want COSIGNED)", failures)

    # --- e: a full, well-formed refs string parses to the item id + both witness kinds -----------
    re_ = parse_item_refs("panel-item:680:A1 row:681 work:kr-titration-design-exploration", 680)
    want_e = ("A1", [("row", "681"), ("work", "kr-titration-design-exploration")])
    check("e-parse-full-refs-string", re_ == want_e,
          f"parse_item_refs(...) = {re_!r} (want {want_e!r})", failures)

    # --- g: one of two substantive witnesses individually cosigned -> PARTIAL --------------------
    rg = derive_status(False, [
        WitnessFacts("row", "681", True, True, 681, True),
        WitnessFacts("row", "716", True, True, 716, False),
    ])
    check("g-partial-one-of-two", rg == "PARTIAL",
          f"derive_status(False, [one cosigned, one not]) = {rg!r} (want PARTIAL)", failures)

    # --- h: every substantive witness individually cosigned -> COSIGNED (equivalence branch) -----
    rh = derive_status(False, [
        WitnessFacts("row", "681", True, True, 681, True),
        WitnessFacts("row", "716", True, True, 716, True),
    ])
    check("h-cosigned-all-witnesses", rh == "COSIGNED",
          f"derive_status(False, [both cosigned]) = {rh!r} (want COSIGNED)", failures)

    # --- i: two DIFFERENT item ids, no collision -- each a length-1 group ------------------------
    ri = group_item_rows((("A1", 812), ("A2", 900)))
    check("i-no-collision-distinct-items", ri == {"A1": (812,), "A2": (900,)},
          f"group_item_rows(((A1,812),(A2,900))) = {ri!r} (want {{'A1': (812,), 'A2': (900,)}})", failures)

    # --- j (r4/round-3): the anchored parser distinguishes a prefix-adjacent item-id pair ---------
    # "A1" is a literal substring of "A10"'s own panel-item token -- the exact shape the round-3
    # finding named for the write side and the round-4 finding named for the read-side aggregate.
    # This is the ONE function both decomposition_items (read) and the WP-3 seed script (write)
    # call to answer "does refs carry item <iid>", so this single case covers the read/write
    # divergence class end to end (spec sec 10).
    rj_item_id, rj_witnesses = parse_item_refs("panel-item:680:A10 row:900", 680)
    ok_j = rj_item_id == "A10" and rj_item_id != "A1" and rj_witnesses == [("row", "900")]
    check("j-prefix-adjacent-item-ids-distinct", ok_j,
          f"parse_item_refs('panel-item:680:A10 row:900', 680) -> item_id={rj_item_id!r} "
          f"(want == 'A10' and != 'A1'), witnesses={rj_witnesses!r}", failures)

    print()
    if failures:
        print(f"FAILURES ({len(failures)}): {failures}")
        return 1
    print("ALL CASES OK -- derive_status/group_item_rows/parse_item_refs both-polarity proof clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
