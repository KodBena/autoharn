#!/usr/bin/env python3
"""run_fixtures_breaker.py -- both-polarity proof for hooks/stop_clean_exit.py's s29 DEBT-TYPE
CONVERSION extension (`_debt_identity()` / the identity-subset branch in `_breaker_transition()`),
sibling to run_fixtures.py in this same directory (which proves the kernel/led side of s29;
this file proves the hook side named in the commission's own words: "the stop_clean_exit
conversion-inherit extension with fixture").

REAL, not mocked: imports `hooks/stop_clean_exit.py` directly (the actual module under test, not a
reimplementation of its logic) and calls `_debt_identity()` / `_breaker_transition()` -- the exact
functions the live hook runs -- against constructed `entries`/`st` values shaped exactly as
`_collect_debt()` produces them (verified against this directory's own `run_fixtures.py` case e,
which shows `led work review-gap` producing the underlying rows `_collect_debt()` reads).

Cases:
  a-identity-normalizes-conversion-pair  -- `_debt_identity("work_open:X")` ==
                                             `_debt_identity("work_review_deferred:X")` (the ONE
                                             conversion pair this delta names) and both differ from
                                             an unrelated slug's identity.
  b-conversion-inherits-breaker          -- the CORE proof (spec Element B: "hooks/
                                             stop_clean_exit.py inherits breaker state over it
                                             exactly as it already inherits over strict-subset
                                             shrinkage"): prior state = {work_open:item-x}, count=1;
                                             current entries = {work_review_deferred:item-x} (the
                                             SAME slug, converted type, same set SIZE -- so the
                                             PRE-EXISTING raw-string strict-subset check alone would
                                             NOT catch this, proving the identity check is doing
                                             real work, not riding along on the old rule) ->
                                             `_breaker_transition` returns 2 (inherited), NOT 1.
  c-genuinely-new-debt-still-resets      -- prior state = {work_open:item-x}, count=1; current
                                             entries = {work_open:item-x, work_open:item-y} (a
                                             SECOND, genuinely new slug alongside the first) ->
                                             `_breaker_transition` returns 1 (the fix narrows the
                                             reset condition, it does not remove it -- unchanged
                                             behavior for real new debt, the negative control).
  d-literal-shrinkage-still-inherits     -- the PRE-EXISTING behavior (unrelated to s29) is
                                             unperturbed by this extension: prior=
                                             {work_open:item-x, work_open:item-y}, count=3; current=
                                             {work_open:item-x} (item-y's debt resolved outright,
                                             no conversion involved) -> returns 4 (inherited via the
                                             ORIGINAL raw-string strict-subset branch, still first
                                             in line before the new identity branch ever runs).

Usage: python3 seen-red/s29-obligation-item-key-and-typed-close/run_fixtures_breaker.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "hooks"))
import stop_clean_exit as sce  # noqa: E402


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def main() -> int:
    failures: list[str] = []

    # --- a: identity normalization ------------------------------------------------------------
    id_open = sce._debt_identity("work_open:item-x")
    id_deferred = sce._debt_identity("work_review_deferred:item-x")
    id_unrelated = sce._debt_identity("work_open:item-y")
    id_other_class = sce._debt_identity("review_gap:42")
    ok_a = (id_open == id_deferred and id_open != id_unrelated
            and id_other_class == "review_gap:42")
    check("a-identity-normalizes-conversion-pair", ok_a,
          f"identity(work_open:item-x)={id_open!r} identity(work_review_deferred:item-x)={id_deferred!r} "
          f"(equal={id_open == id_deferred}); identity(work_open:item-y)={id_unrelated!r} "
          f"(differs={id_open != id_unrelated}); identity(review_gap:42)={id_other_class!r} (untouched)",
          failures)

    # --- b: the core conversion-inherits-breaker proof ----------------------------------------
    st_b = {"debt_hash": "OLD_HASH", "count": 1, "entries": ["work_open:item-x"]}
    entries_b = ["work_review_deferred:item-x"]
    new_hash_b = sce._debt_hash(entries_b)
    # sanity: the debt_hash genuinely changed (else this would trivially hit the first branch,
    # not the identity-subset branch we mean to exercise)
    assert new_hash_b != st_b["debt_hash"]
    # sanity: the RAW-STRING strict-subset check alone does NOT catch this (same set size, no
    # string is a subset of the other) -- proves the identity branch is doing real work
    raw_subset = set(entries_b) < set(st_b["entries"])
    result_b = sce._breaker_transition(st_b, entries_b, new_hash_b)
    ok_b = (not raw_subset) and result_b == 2
    check("b-conversion-inherits-breaker", ok_b,
          f"raw_string_subset_alone={raw_subset} (expect False -- proves the identity check is load-bearing) "
          f"_breaker_transition(...)={result_b} (expect 2, inherited from prior count=1)", failures)

    # --- c: genuinely new debt (a second, unrelated slug) still resets to 1 -------------------
    st_c = {"debt_hash": "OLD_HASH", "count": 1, "entries": ["work_open:item-x"]}
    entries_c = ["work_open:item-x", "work_open:item-y"]
    new_hash_c = sce._debt_hash(entries_c)
    result_c = sce._breaker_transition(st_c, entries_c, new_hash_c)
    ok_c = result_c == 1
    check("c-genuinely-new-debt-still-resets", ok_c,
          f"_breaker_transition(...)={result_c} (expect 1 -- a genuinely new slug's debt is not "
          f"an identity the prior state names)", failures)

    # --- d: pre-existing literal-shrinkage inheritance is unperturbed --------------------------
    st_d = {"debt_hash": "OLD_HASH", "count": 3, "entries": ["work_open:item-x", "work_open:item-y"]}
    entries_d = ["work_open:item-x"]
    new_hash_d = sce._debt_hash(entries_d)
    result_d = sce._breaker_transition(st_d, entries_d, new_hash_d)
    ok_d = result_d == 4
    check("d-literal-shrinkage-still-inherits", ok_d,
          f"_breaker_transition(...)={result_d} (expect 4 -- the PRE-EXISTING raw-string "
          f"strict-subset branch, unperturbed by this delta's addition)", failures)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- hooks/stop_clean_exit.py s29 debt-type CONVERSION proof (identity "
          "normalizes the work_open<->work_review_deferred pair / a same-size type-converted debt "
          "set inherits the breaker / genuinely new debt still resets / pre-existing literal-"
          "shrinkage inheritance is unperturbed).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
