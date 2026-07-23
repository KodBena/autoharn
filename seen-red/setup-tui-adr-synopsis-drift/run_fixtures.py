#!/usr/bin/env python3
"""seen-red/setup-tui-adr-synopsis-drift/run_fixtures.py -- both-polarity proof of
`tools/setup_tui/durable_decisions.py`'s ADR-synopsis drift backstop (maintainer question,
2026-07-22: "the ADR-adoption catalog derives live from law/adr/*.md, but tools/setup_tui/data/
adr_synopses.toml is static and already stale twice today"), census-registered in
gates/fixture_census.py.

Same house idiom as `seen-red/setup-tui-feature-facts-drift` (feature_facts.check_registry's own
injectable comparator, WF2): `durable_decisions.check_adr_synopsis_freshness(adrs=..., hashes=...,
read_bytes=...)` accepts a SYNTHETIC `adrs`/`hashes`/`read_bytes` so a fixture can observe both
red legs without mutating this module's real globals (`content.ADR_SYNOPSIS_HASHES`, the real
`law/adr/*.md` files) -- no monkeypatching, no real file writes.

Cases:
  1. GREEN leg -- the REAL catalog vs the REAL recorded hashes agrees: `check_adr_synopsis_
     freshness()` with no arguments returns `([], [])`. This IS this fixture's own proof of
     itself staying green against an unmodified corpus (every 20 ADRs' hashes were freshly
     stamped this session).
  2. RED leg A (MISSING) -- a synthetic `adrs` list names an ADR number with NO entry in the
     (real) hash dict; `check_adr_synopsis_freshness` must report it in `missing`, and
     `validate_adr_synopsis_freshness` (the REAL, wired, no-arguments entry point) must REFUSE
     (`AdrSynopsisMissingError`) when a synthetic hash dict is substituted via monkeypatching
     `content.ADR_SYNOPSIS_HASHES` for the duration of one call, restored immediately after.
  3. RED leg B (STALE) -- a synthetic `read_bytes` returns DIFFERENT bytes than what the real
     `source_sha256` was stamped against; `check_adr_synopsis_freshness` must report it in
     `stale` (an `AdrSynopsisDrift` naming both the declared and actual hash), and this is
     NEVER a refusal -- `validate_adr_synopsis_freshness` must still RETURN (not raise) when
     every ADR has SOME hash recorded, even a stale one (case 4).
  4. GREEN (the maintainer's own commission, done): `validate_adr_synopsis_freshness()` -- the
     REAL, wired, no-substitution call -- returns an EMPTY tuple: all 20 ADR synopses are fresh,
     confirming the 2026-07-22 re-derivation + hash-stamping pass (0019's own four-rule text,
     0003 confirmed matching its current post-strike text, all 20 hashes stamped, 0001 kept
     pending-review with its own hash stamped so it is stale-checked like every other entry).

Zero residue: no real file is ever written by this fixture; `content.ADR_SYNOPSIS_HASHES` is
monkeypatched only within a `try`/`finally` and always restored. Lazy imports banned.

Usage: python3 seen-red/setup-tui-adr-synopsis-drift/run_fixtures.py
Exit 0 if every case matches its expected polarity; 1 otherwise."""
from __future__ import annotations

import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from tools.setup_tui import content, durable_decisions  # noqa: E402


def case_1_green_real_catalog() -> None:
    missing, stale = durable_decisions.check_adr_synopsis_freshness()
    assert missing == [], f"expected zero MISSING synopses against the real catalog, got {missing}"
    assert stale == [], f"expected zero STALE synopses against the real catalog, got {stale}"
    print("case 1 ok (GREEN): the real 20-ADR catalog agrees with the real recorded hashes -- "
          "zero missing, zero stale")


def case_2_red_missing() -> None:
    real_adrs = durable_decisions.list_adrs()
    synthetic_adrs = list(real_adrs) + [("9999", "a synthetic ADR with no synopsis at all",
                                          "law/adr/9999-does-not-exist.md")]
    missing, stale = durable_decisions.check_adr_synopsis_freshness(adrs=synthetic_adrs)
    assert missing == ["9999"], f"expected ['9999'] reported MISSING, got {missing}"
    print(f"case 2 ok (RED leg A, MISSING): a synthetic ADR number with no synopsis entry at "
          f"all is reported MISSING: {missing}")

    # The REAL, wired, no-arguments entry point must REFUSE the same way -- substitute a
    # synthetic hash dict (real ADRs, one deliberately REMOVED) for the duration of one call.
    original_hashes = content.ADR_SYNOPSIS_HASHES
    synthetic_hashes = dict(original_hashes)
    removed_number = next(iter(synthetic_hashes))
    del synthetic_hashes[removed_number]
    content.ADR_SYNOPSIS_HASHES = synthetic_hashes
    try:
        try:
            durable_decisions.validate_adr_synopsis_freshness()
            raise AssertionError("expected AdrSynopsisMissingError, got no exception at all")
        except durable_decisions.AdrSynopsisMissingError as exc:
            assert removed_number in str(exc), (
                f"expected the refusal to NAME the missing ADR {removed_number!r}, got: {exc}")
            print(f"case 2b ok (RED, real entry point): validate_adr_synopsis_freshness() "
                  f"REFUSES (AdrSynopsisMissingError) when ADR-{removed_number}'s own hash is "
                  f"absent, naming it: {str(exc)[:120]}...")
    finally:
        content.ADR_SYNOPSIS_HASHES = original_hashes


def case_3_red_stale() -> None:
    real_adrs = durable_decisions.list_adrs()

    def fake_read_bytes(relpath: str) -> bytes:
        return b"this is deliberately DIFFERENT content than what the real hash was stamped against"

    missing, stale = durable_decisions.check_adr_synopsis_freshness(
        adrs=real_adrs, read_bytes=fake_read_bytes)
    assert missing == [], f"expected zero MISSING (every real ADR has a hash) -- got {missing}"
    assert len(stale) == len(real_adrs), (
        f"expected EVERY entry reported STALE against fabricated bytes -- got {len(stale)} of "
        f"{len(real_adrs)}")
    sample = stale[0]
    assert sample.declared_sha256 != sample.actual_sha256, "expected declared != actual on a stale entry"
    print(f"case 3 ok (RED leg B, STALE): {len(stale)} synopsis entries report STALE against "
          f"fabricated ADR bytes -- e.g. ADR-{sample.number}: declared "
          f"{sample.declared_sha256[:12]}... != actual {sample.actual_sha256[:12]}...")

    # STALE must NEVER be a refusal from the real entry point when every ADR has SOME hash --
    # substitute a hash dict where every value is deliberately WRONG (still present, just stale).
    original_hashes = content.ADR_SYNOPSIS_HASHES
    stale_hashes = {number: "0" * 64 for number in original_hashes}
    content.ADR_SYNOPSIS_HASHES = stale_hashes
    try:
        result = durable_decisions.validate_adr_synopsis_freshness()
        assert len(result) == len(original_hashes), (
            f"expected every entry reported stale (not raised), got {len(result)} of "
            f"{len(original_hashes)}")
        print(f"case 3b ok (GREEN, real entry point does NOT refuse on stale): "
              f"validate_adr_synopsis_freshness() RETURNS {len(result)} stale entries instead "
              f"of raising -- a stale synopsis warns, it does not brick setup")
    finally:
        content.ADR_SYNOPSIS_HASHES = original_hashes


def case_4_green_real_wired_call() -> None:
    result = durable_decisions.validate_adr_synopsis_freshness()
    assert result == (), (
        f"expected the REAL, wired validate_adr_synopsis_freshness() to return an EMPTY tuple "
        f"(the maintainer's own commission: re-derive 0019, confirm 0003, stamp all 20 hashes) "
        f"-- got {result}")
    print("case 4 ok (GREEN, the maintainer's own commission): validate_adr_synopsis_freshness() "
          "-- the real, wired, no-substitution call -- returns zero stale entries: all 20 ADR "
          "synopses (0019's re-derived four-rule text, 0003 confirmed current, every hash "
          "stamped this session, 0001 pending-review but hash-stamped like the rest) are fresh")


def main() -> None:
    case_1_green_real_catalog()
    case_2_red_missing()
    case_3_red_stale()
    case_4_green_real_wired_call()
    print("ALL CASES OK -- durable_decisions.check_adr_synopsis_freshness/"
          "validate_adr_synopsis_freshness: GREEN against the real, freshly-stamped catalog, "
          "RED-first for a MISSING synopsis (construction-time refusal, naming the ADR) and a "
          "STALE synopsis (loud warning naming both hashes, never a refusal), both via the SAME "
          "injectable-comparator house idiom seen-red/setup-tui-feature-facts-drift established.")


if __name__ == "__main__":
    main()
