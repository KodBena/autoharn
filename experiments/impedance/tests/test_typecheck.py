#!/usr/bin/env python
"""tests/test_typecheck.py — the mechanized closure claim (ADR-0011 Rule 1 / ADR-0009 Rule 5).

The four impedances being UNCONSTRUCTABLE is not asserted in prose — it is a TEST that runs
`mypy --strict` and reads the diagnostics:

  * the whole package + the MEDIATED demo type-check CLEAN (the happy path);
  * every deliberate crossing in demo/mismatches.py emits its predicted error code, and NOTHING
    else on an untagged line (the lib/device/dtype/shape/capability seams + the device-MODEL
    forge closures (f)/(g) and the in-library co-residence case (h));
  * the carrier-discipline negative fixture emits its predicted codes (non-coercible /
    non-constructable).
"""

from __future__ import annotations

from collections.abc import Callable


def _assert_negative_fixture(
    target: str,
    mypy_errors: Callable[[str], dict[int, set[str]]],
    expect_tags: Callable[[str], dict[int, str]],
) -> None:
    errors = mypy_errors(target)
    tags = expect_tags(target)
    assert tags, f"no EXPECT tags found in {target}"
    for line, code in tags.items():
        assert line in errors, f"{target}:{line} expected [{code}] but NO error fired (errors: {errors})"
        assert code in errors[line], f"{target}:{line} expected [{code}], got {sorted(errors[line])}"
    # every error must land on a tagged line — no stray, unexpected impedance leaks through.
    stray = {ln: sorted(cs) for ln, cs in errors.items() if ln not in tags}
    assert not stray, f"unexpected mypy errors in {target} on untagged lines: {stray}"


def test_clean_gate_passes(clean_gate_ok: Callable[[], object]) -> None:
    proc = clean_gate_ok()  # type: ignore[call-arg]
    assert proc.returncode == 0, f"clean gate failed:\n{proc.stdout}\n{proc.stderr}"  # type: ignore[attr-defined]


def test_impedance_crossings_dont_typecheck(
    mypy_errors: Callable[[str], dict[int, set[str]]],
    expect_tags: Callable[[str], dict[int, str]],
) -> None:
    # the five seam crossings + the two device-MODEL forge closures (D1) + the in-library
    # co-residence case (D4): each emits its tagged code, nothing strays onto an untagged line.
    _assert_negative_fixture("demo/mismatches.py", mypy_errors, expect_tags)


def test_carrier_discipline_regression(
    mypy_errors: Callable[[str], dict[int, set[str]]],
    expect_tags: Callable[[str], dict[int, str]],
) -> None:
    _assert_negative_fixture("tests/fixtures/carrier_neg.py", mypy_errors, expect_tags)
