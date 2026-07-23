#!/usr/bin/env python3
"""Both-polarity fixture for gates/deep_walk_recursion_guard.py (boundary-recursion-net-
single-invariant, ledger row 1628, re-asserted from autoharn1).

GREEN: the real serving/boundary_service.py passes -- `_guard_recursion` is the only place
`RecursionError` is ever caught in that file.

RED (bypass): a synthetic FOURTH deep-walk site, appended to a throwaway copy of the real
module, that bypasses `_guard_recursion` by open-coding its own `except RecursionError` clause
-- exactly the shape this gate exists to catch (row 1628's own words: "a fourth traversal site
added later could still miss it"). Refused, naming the offending line.

RED (superclass evasion, reviewer-demonstrated): a synthetic site that wraps a deep-walk call
in `except RuntimeError` -- RecursionError's OWN SUPERCLASS -- never spelling `RecursionError`
at all, so the bypass check above (which only matches the literal name) used to sail through
clean. Also covers the bare `except:` and `except Exception` forms of the same evasion, and
confirms the `# deep-walk-recursion-guard-superclass-reviewed:` waiver comment lets a reviewed
catch through, and that an UNRELATED `except Exception` (wrapping no deep-walk call at all)
stays clean -- the scoping-to-censused-sites check.

Runs against throwaway tempfile copies; zero residue in the repo itself."""
from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "..")
GATE = os.path.join(REPO, "gates", "deep_walk_recursion_guard.py")
TARGET = os.path.join(REPO, "serving", "boundary_service.py")

# A synthetic fourth traversal, never committed to the real module: it bypasses the shared
# helper by writing its OWN except-RecursionError clause rather than routing through
# `_guard_recursion`, the exact defect class row 1628 names.
SYNTHETIC_BYPASS_SITE = '''

def _fourth_deep_walk_site_synthetic_bypass(payload):
    """RED-fixture-only: a fourth traversal that bypasses _guard_recursion by open-coding its
    own except clause. Never present in the real module -- appended only to a throwaway copy
    by this fixture."""
    try:
        return list(_iter_strings(payload))
    except RecursionError as e:
        axis, detail = _classify_parse_failure(e)
        return None, axis, detail
'''

# The reviewer's demonstrated evasion: wraps a censused deep-walk call (`_guard_recursion`
# itself) in `except RuntimeError` -- RecursionError's superclass -- so RecursionError is
# caught by inheritance without the except clause ever naming it. Also exercises the bare
# `except:` and `except Exception` forms, a WAIVED site (must stay clean), and an unrelated
# `except Exception` wrapping no deep-walk call at all (must ALSO stay clean -- the
# scoping-to-censused-sites check, not "every Exception catch in the file").
SYNTHETIC_SUPERCLASS_EVASION_SITES = '''

def _fifth_deep_walk_site_runtimeerror_evasion(payload):
    """RED-fixture-only: catches RuntimeError (RecursionError's own superclass) around a
    _guard_recursion call, never spelling RecursionError -- the reviewer's demonstrated
    evasion of the literal-name-only check."""
    try:
        return _guard_recursion(_iter_strings, payload)
    except RuntimeError as e:
        return None


def _sixth_deep_walk_site_bare_except_evasion(payload):
    """RED-fixture-only: a bare `except:` around a direct json.loads call -- the widest form
    of the same superclass-catch evasion."""
    try:
        return json.loads(payload)
    except:
        return None


def _seventh_deep_walk_site_waived_superclass_catch(payload):
    """RED-fixture-only, but must stay CLEAN: a RuntimeError catch around a deep-walk call
    that carries the waiver comment -- the annotation escape hatch, not a silent weakening."""
    try:
        return _representability_axis_failure(payload)
    except RuntimeError as e:  # deep-walk-recursion-guard-superclass-reviewed: fixture-only demonstration of the waiver token
        return None


def _unrelated_broad_catch_no_deep_walk(x):
    """RED-fixture-only, but must stay CLEAN: an ordinary except-Exception catch wrapping NO
    deep-walk call at all -- confirms the check is scoped to censused sites, not every catch."""
    try:
        return 1 / x
    except Exception:
        return None
'''


def main() -> int:
    # GREEN: the real file, unmodified.
    green = subprocess.run([sys.executable, GATE, TARGET], capture_output=True, text=True)
    assert green.returncode == 0, (
        f"GREEN expected exit 0 on the real module, got {green.returncode}: {green.stdout}")
    assert green.stdout == "", f"GREEN expected silent pass, got: {green.stdout}"
    print("GREEN ok: serving/boundary_service.py passes -- _guard_recursion is the only "
          "except-RecursionError site")

    # RED: append the synthetic bypass to a throwaway copy and re-run the gate against it.
    src = open(TARGET, encoding="utf-8").read()
    red_src = src + SYNTHETIC_BYPASS_SITE
    ast.parse(red_src)  # sanity: the synthetic fixture itself must be valid Python
    fd, red_path = tempfile.mkstemp(prefix="deep-walk-recursion-guard-red-", suffix=".py")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(red_src)
        red = subprocess.run([sys.executable, GATE, red_path], capture_output=True, text=True)
        assert red.returncode == 1, (
            f"RED expected exit 1 on the synthetic bypass, got {red.returncode}: {red.stdout}")
        assert "bypassing the single" in red.stdout, red.stdout
        assert "boundary-recursion-net-single-invariant" in red.stdout, red.stdout
        print("RED  ok: synthetic fourth bypassing site refused:")
        for line in red.stdout.splitlines():
            if "bypassing" in line:
                print(f"  {line}")
    finally:
        os.unlink(red_path)

    # RED: the reviewer's demonstrated superclass-catch evasions -- RuntimeError/bare-except
    # around a deep-walk call must now refuse; a WAIVED equivalent catch and an unrelated
    # except-Exception (no deep-walk call in its try body) must stay clean alongside them.
    red2_src = src + SYNTHETIC_SUPERCLASS_EVASION_SITES
    ast.parse(red2_src)  # sanity: the synthetic fixture itself must be valid Python
    fd, red2_path = tempfile.mkstemp(prefix="deep-walk-recursion-guard-red-superclass-",
                                      suffix=".py")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(red2_src)
        red2 = subprocess.run([sys.executable, GATE, red2_path], capture_output=True, text=True)
        assert red2.returncode == 1, (
            f"RED expected exit 1 on the superclass-catch evasions, got {red2.returncode}: "
            f"{red2.stdout}")
        assert "catching RuntimeError catches RecursionError by inheritance" in red2.stdout, \
            red2.stdout
        # Exactly the two unwaived evasion sites are flagged -- the waived RuntimeError catch
        # and the unrelated except-Exception (no deep-walk call) must NOT appear.
        assert red2.stdout.count("wraps a deep-walk call") == 2, red2.stdout
        assert "_fifth_deep_walk_site_runtimeerror_evasion" not in red2.stdout  # names aren't
        # printed, but the line numbers must correspond only to the two unwaived sites -- checked
        # via the exact count above plus the two textual markers below.
        assert "`except RuntimeError`" in red2.stdout, red2.stdout
        assert "bare `except:`" in red2.stdout, red2.stdout
        print("RED  ok: superclass-catch evasions (except RuntimeError / bare except) refused, "
              "waived site and unrelated except-Exception stayed clean:")
        for line in red2.stdout.splitlines():
            if "wraps a deep-walk call" in line:
                print(f"  {line}")
    finally:
        os.unlink(red2_path)

    print("ALL CASES OK -- deep-walk-recursion-guard both polarities, zero residue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
