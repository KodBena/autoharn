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

RED (attribute-qualified superclass evasion, Finding B, 2026-07-23): `except builtins.
RuntimeError:` around a deep-walk call -- the same superclass-catch evasion spelled with an
attribute-qualified name, which `_names_superclass_evasion` used to miss (it only matched bare
`ast.Name`/`ast.Tuple`). Must now refuse.

DOCUMENTED-GAP (Finding B, 2026-07-23, asserted PASS on purpose): `E = RuntimeError` at module
scope, then `except E:` around a deep-walk call -- the ALIASED-name evasion. This gate does NOT
close this (full scope/assignment tracking is out of proportion for a census gate); it is named
in the gate's own docstring as a KNOWN SILENT GAP. This fixture asserts the CURRENT pass
behavior, with this comment pointing at that docstring limit, so a future close of the gap
flips this assertion deliberately rather than an unnoticed regression flipping it silently.

GREEN (multi-line waived clause, Finding C, 2026-07-23): a waived superclass catch whose except
TYPE expression spans multiple lines (so `ExceptHandler.lineno`, the `except` keyword's own
line, is NOT the line the waiver comment naturally sits on) -- the waiver comment on the line
just before the handler body's first statement must still be found, not just on the `except`
keyword's own line.

STAGED-VS-TREE (Finding A, 2026-07-23): a throwaway git repo proves the gate now judges the
STAGED bytes by default, not the working tree -- `git add` a violating copy, then restore a
clean copy to the working tree WITHOUT re-staging: the gate (no `--tree` flag, default mode)
must still refuse, because the commit would still embed the staged violation.

The tempfile-based cases above pass `--tree` explicitly: they are throwaway files that were
never staged into (and in general are not even inside) this repository's git index, so this
documents the manual/fixture read mode rather than depending on the "not staged, fall back to
tree" default behavior to happen to apply.

Runs against throwaway tempfile copies (and one throwaway git repo for the staged-bytes case);
zero residue in the repo itself."""
from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

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

# Finding B (2026-07-23): the attribute-qualified spelling of the same superclass-catch evasion
# -- `except builtins.RuntimeError:` never spells a bare `RuntimeError` Name, so the old
# Name/Tuple-only check missed it. Must now refuse, same as the bare-name form above.
SYNTHETIC_ATTRIBUTE_QUALIFIED_EVASION = '''

import builtins


def _eighth_deep_walk_site_attribute_qualified_evasion(payload):
    """RED-fixture-only: catches builtins.RuntimeError (attribute-qualified) around a
    _guard_recursion call -- the same superclass-catch evasion as _fifth_..., spelled so the
    old Name/Tuple-only check missed it."""
    try:
        return _guard_recursion(_iter_strings, payload)
    except builtins.RuntimeError as e:
        return None
'''

# Finding B (2026-07-23), DOCUMENTED GAP: an ALIASED exception name. `E = RuntimeError` then
# `except E:` around a deep-walk call passes this gate SILENTLY -- a known, named limit (see
# this gate's own docstring), not something this fixture treats as a defect. Asserted as a
# PASS on purpose, with this comment pointing at the docstring limit, so a future close of the
# gap flips this assertion deliberately rather than a silent regression flipping it unnoticed.
SYNTHETIC_ALIAS_DOCUMENTED_GAP = '''

E = RuntimeError


def _ninth_deep_walk_site_aliased_exception_documented_gap(payload):
    """DOCUMENTED-GAP-fixture-only: catches E (an alias of RuntimeError) around a
    _guard_recursion call. This gate does NOT trace the assignment `E = RuntimeError` back to
    RuntimeError -- a KNOWN SILENT GAP named in the gate's own docstring, not a defect this
    fixture is asserting should be caught. Kept PASSING on purpose."""
    try:
        return _guard_recursion(_iter_strings, payload)
    except E as e:
        return None
'''

# Finding C (2026-07-23): a waived superclass catch whose except TYPE expression spans multiple
# lines -- ExceptHandler.lineno is the `except` keyword's own line, so a waiver comment placed
# naturally right before the colon (the line just before the handler body's first statement)
# used to be invisible to the old single-line-only check, over-refusing a genuinely-waived
# clause. Must stay CLEAN.
SYNTHETIC_MULTILINE_WAIVED_CLAUSE = '''

def _tenth_deep_walk_site_multiline_waived_clause(payload):
    """GREEN-fixture-only: a RuntimeError catch around a deep-walk call whose except-clause
    type expression spans multiple lines, with the waiver comment on the line just before the
    handler body's first statement -- must stay clean (Finding C)."""
    try:
        return _guard_recursion(_iter_strings, payload)
    except (
        RuntimeError
    ):  # deep-walk-recursion-guard-superclass-reviewed: fixture-only multi-line waiver
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
        red = subprocess.run([sys.executable, GATE, "--tree", red_path], capture_output=True, text=True)
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
        red2 = subprocess.run([sys.executable, GATE, "--tree", red2_path], capture_output=True, text=True)
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

    # RED: Finding B, attribute-qualified superclass evasion (`except builtins.RuntimeError:`)
    # must refuse, same as the bare-name form.
    red3_src = src + SYNTHETIC_ATTRIBUTE_QUALIFIED_EVASION
    ast.parse(red3_src)
    fd, red3_path = tempfile.mkstemp(prefix="deep-walk-recursion-guard-red-attr-", suffix=".py")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(red3_src)
        red3 = subprocess.run([sys.executable, GATE, "--tree", red3_path], capture_output=True, text=True)
        assert red3.returncode == 1, (
            f"RED expected exit 1 on the attribute-qualified evasion, got {red3.returncode}: "
            f"{red3.stdout}")
        assert "wraps a deep-walk call" in red3.stdout, red3.stdout
        print("RED  ok: attribute-qualified superclass evasion (except builtins.RuntimeError) "
              "refused:")
        for line in red3.stdout.splitlines():
            if "wraps a deep-walk call" in line:
                print(f"  {line}")
    finally:
        os.unlink(red3_path)

    # DOCUMENTED-GAP: the aliased-exception evasion (`E = RuntimeError` then `except E:`)
    # passes SILENTLY -- a known, named limit, not a defect. Asserted PASS on purpose; see this
    # gate's own docstring's KNOWN SILENT GAP entry. A future close of the gap must flip this
    # assertion deliberately.
    gap_src = src + SYNTHETIC_ALIAS_DOCUMENTED_GAP
    ast.parse(gap_src)
    fd, gap_path = tempfile.mkstemp(prefix="deep-walk-recursion-guard-documented-gap-alias-",
                                     suffix=".py")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(gap_src)
        gap = subprocess.run([sys.executable, GATE, "--tree", gap_path], capture_output=True, text=True)
        assert gap.returncode == 0, (
            f"DOCUMENTED-GAP expected exit 0 (aliased-exception evasion is a named, NOT-closed "
            f"gap), got {gap.returncode}: {gap.stdout}")
        assert gap.stdout == "", f"DOCUMENTED-GAP expected silent pass, got: {gap.stdout}"
        print("DOCUMENTED-GAP ok: aliased-exception evasion (E = RuntimeError; except E:) "
              "still passes silently -- named in the gate's own docstring, not closed here")
    finally:
        os.unlink(gap_path)

    # GREEN: Finding C, a multi-line except-clause type expression with the waiver comment on
    # the line just before the handler body's first statement must stay clean.
    multiline_src = src + SYNTHETIC_MULTILINE_WAIVED_CLAUSE
    ast.parse(multiline_src)
    fd, multiline_path = tempfile.mkstemp(prefix="deep-walk-recursion-guard-multiline-waiver-",
                                           suffix=".py")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(multiline_src)
        ml = subprocess.run([sys.executable, GATE, "--tree", multiline_path], capture_output=True, text=True)
        assert ml.returncode == 0, (
            f"GREEN expected exit 0 on the multi-line waived clause, got {ml.returncode}: "
            f"{ml.stdout}")
        assert ml.stdout == "", f"GREEN expected silent pass, got: {ml.stdout}"
        print("GREEN ok: multi-line except-clause waiver (comment before the handler body's "
              "first statement, not on the `except` keyword's own line) recognized")
    finally:
        os.unlink(multiline_path)

    # RED: Finding A, staged-vs-tree. A throwaway git repo proves the gate judges the STAGED
    # bytes by default: stage a violating copy, then restore a clean copy to the working tree
    # WITHOUT re-staging -- the gate (no --tree flag) must still refuse.
    with tempfile.TemporaryDirectory(prefix="deep-walk-recursion-guard-staged-vs-tree-") as repo_dir:
        subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True)
        subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=repo_dir, check=True)
        subprocess.run(["git", "config", "user.name", "fixture"], cwd=repo_dir, check=True)
        target_rel = "serving/boundary_service.py"
        target_abs = os.path.join(repo_dir, target_rel)
        os.makedirs(os.path.dirname(target_abs), exist_ok=True)
        # Commit the clean real file first, so the repo has a baseline history.
        with open(target_abs, "w", encoding="utf-8") as f:
            f.write(src)
        subprocess.run(["git", "add", target_rel], cwd=repo_dir, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "baseline"], cwd=repo_dir, check=True)
        # Stage the violating bypass, then restore the clean file in the WORKING TREE only --
        # `git add` already copied the violating bytes into the index; overwriting the tree
        # file afterward does not touch the index.
        with open(target_abs, "w", encoding="utf-8") as f:
            f.write(red_src)
        subprocess.run(["git", "add", target_rel], cwd=repo_dir, check=True)
        with open(target_abs, "w", encoding="utf-8") as f:
            f.write(src)
        staged = subprocess.run(
            [sys.executable, GATE, target_abs], cwd=repo_dir, capture_output=True, text=True)
        assert staged.returncode == 1, (
            f"STAGED-VS-TREE expected exit 1 (staged bytes still carry the violation even "
            f"though the tree was restored clean), got {staged.returncode}: {staged.stdout}")
        assert "bypassing the single" in staged.stdout, staged.stdout
        print("RED  ok: staged-vs-tree -- violation staged, tree restored clean, default "
              "(no --tree) read still refuses on the STAGED bytes:")
        for line in staged.stdout.splitlines():
            if "bypassing" in line:
                print(f"  {line}")
        # Sanity: --tree (working-tree mode) now reads the RESTORED CLEAN tree file and passes
        # -- confirming the two modes really do read different bytes, not a fluke.
        tree_mode = subprocess.run(
            [sys.executable, GATE, "--tree", target_abs], cwd=repo_dir, capture_output=True, text=True)
        assert tree_mode.returncode == 0, (
            f"STAGED-VS-TREE sanity: --tree should read the restored clean tree file, got "
            f"{tree_mode.returncode}: {tree_mode.stdout}")
        print("     ok: --tree (working-tree mode) reads the restored clean file and passes -- "
              "the two read modes genuinely differ")

    print("ALL CASES OK -- deep-walk-recursion-guard both polarities, zero residue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
