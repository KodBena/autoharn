#!/usr/bin/env python3
"""bounds_kernel_drift -- ADR-0012 P1's cross-layer form (ledger row 1514 item 2): asserts the
SERVICE layer's bound vocabulary (serving/bounds.py) has not drifted from its KERNEL-side twin,
for every named bound that has one.

Motivation (the finding this gate exists to close): before serving/bounds.py's single home, the
256-byte identity bound and the 1 MiB write-body bound each lived as TWO INDEPENDENT literals --
s65's kernel CHECK said 256, boundary_service.py's own IDENTITY_HEADER_MAX_BYTES said 256,
independently; s51's kernel artifact_size_within_cap CHECK said 1048576, boundary_service.py's
own MAX_WRITE_BODY_BYTES said 1_048_576, independently too -- and nothing detected drift between
either pair. This gate is that detection: it reads the kernel SQL text directly (Python cannot
import SQL) and compares each kernel literal against its service-side named constant.

The extraction is honest TEXT EXTRACTION against a precise anchor -- the CHECK constraint's own
name plus its EXACT clause shape (verified against the live kernel/lineage/*.sql files this gate
targets) -- never a loose/fuzzy regex that could silently match nothing. A fragile anchor that
stops matching (because the kernel file was edited, the constraint renamed/reshaped/moved) is
exactly the false-SILENT failure mode ADR-0002/CLAUDE.md's audit-bias clauses warn against: this
gate FAILS LOUDLY (RuntimeError naming the missing anchor and the file) rather than silently
reporting an "agreement" it never actually checked.

kernel/lineage/*.sql files are FROZEN (this build does not touch their SQL) -- this gate only
READS them as text; it is a service-side-only mechanism the kernel side never has to know about.

Exit 0 clean; exit 1 naming the drifted pair (or the missing anchor). Run from repo root:
python3 gates/bounds_kernel_drift.py
Lazy imports banned -- both the sys.path setup and the `bounds` import below run unconditionally
at module-import time, before any function runs (the same pattern serving/boundary_service.py's
own docstring justifies for the identical reason: gates/no_lazy_imports.py polices this file
too)."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, str(Path(ROOT) / "serving"))
import bounds  # noqa: E402  (serving/bounds.py -- the ONE service-side home this gate checks)

# Anchor 1: kernel/lineage/s65-refusal-attempted-kind.sql's refusal_attempted_kind_length CHECK
# -- the exact two-statement ALTER TABLE ... ADD CONSTRAINT shape as it stands in that file today
# (verified against the live file at authoring time; see this gate's own docstring on why a
# non-match here is a loud failure, never a silent pass).
_S65_PATH = os.path.join(ROOT, "kernel", "lineage", "s65-refusal-attempted-kind.sql")
_S65_ANCHOR = re.compile(
    r"ADD CONSTRAINT refusal_attempted_kind_length CHECK \(\s*"
    r"refusal_attempted_kind IS NULL OR octet_length\(refusal_attempted_kind\) <= (\d+)\);"
)
_S65_ANCHOR_DESC = (
    "ALTER TABLE ... ADD CONSTRAINT refusal_attempted_kind_length CHECK ("
    "refusal_attempted_kind IS NULL OR octet_length(refusal_attempted_kind) <= N);"
)

# Anchor 2: kernel/lineage/s51-artifact-store.sql's artifact_size_within_cap CHECK.
_S51_PATH = os.path.join(ROOT, "kernel", "lineage", "s51-artifact-store.sql")
_S51_ANCHOR = re.compile(
    r"ADD CONSTRAINT artifact_size_within_cap CHECK \(\s*"
    r"size <= (\d+)\);"
)
_S51_ANCHOR_DESC = "ALTER TABLE ... ADD CONSTRAINT artifact_size_within_cap CHECK (size <= N);"


def extract_int(path: str, anchor_re: "re.Pattern[str]", anchor_desc: str) -> int:
    """Reads path's text and extracts the ONE integer the anchor regex captures. FAILS LOUDLY
    (RuntimeError) if the anchor is not found in the file, or if the file itself is missing --
    a fragile regex silently matching nothing is exactly the false-SILENT failure mode this gate
    exists to refuse; a loud crash beats a green gate that never actually compared anything."""
    if not os.path.isfile(path):
        raise RuntimeError(
            f"bounds_kernel_drift: kernel file NOT FOUND at {path!r} -- cannot check drift "
            f"against a bound this gate has no anchor to read. Refusing to report agreement it "
            f"cannot prove.")
    text = Path(path).read_text(encoding="utf-8")
    m = anchor_re.search(text)
    if m is None:
        raise RuntimeError(
            f"bounds_kernel_drift: anchor NOT FOUND in {path!r} -- expected the shape "
            f"{anchor_desc!r}. This means either the kernel file's CHECK constraint was "
            f"renamed/reshaped/moved, or this gate's own regex is stale against a kernel file "
            f"this build does not touch. Refusing to report agreement it cannot prove -- fix "
            f"the anchor (this file) to match the kernel's current shape, never weaken the "
            f"regex to something that would match unrelated text.")
    return int(m.group(1))


def check() -> list[str]:
    """Returns the list of drift problems found (empty == no drift). Each named bound with a
    kernel twin (per serving/bounds.py's own docstrings) gets exactly one comparison here."""
    problems: list[str] = []

    kernel_identity_bound = extract_int(_S65_PATH, _S65_ANCHOR, _S65_ANCHOR_DESC)
    if bounds.IDENTITY_HEADER_MAX_BYTES != kernel_identity_bound:
        problems.append(
            f"DRIFT: serving/bounds.py IDENTITY_HEADER_MAX_BYTES = "
            f"{bounds.IDENTITY_HEADER_MAX_BYTES} but {_S65_PATH}'s own "
            f"refusal_attempted_kind_length CHECK bounds it at {kernel_identity_bound}.")

    kernel_artifact_bound = extract_int(_S51_PATH, _S51_ANCHOR, _S51_ANCHOR_DESC)
    if bounds.MAX_WRITE_BODY_BYTES != kernel_artifact_bound:
        problems.append(
            f"DRIFT: serving/bounds.py MAX_WRITE_BODY_BYTES = {bounds.MAX_WRITE_BODY_BYTES} but "
            f"{_S51_PATH}'s own artifact_size_within_cap CHECK bounds it at "
            f"{kernel_artifact_bound}.")

    return problems


def main() -> int:
    problems = check()
    if problems:
        sys.stderr.write("bounds_kernel_drift: REFUSED\n")
        for p in problems:
            sys.stderr.write(f"  - {p}\n")
        return 1
    print("bounds_kernel_drift: OK -- serving/bounds.py agrees with both kernel-side CHECK twins "
          f"({_S65_PATH}, {_S51_PATH})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
