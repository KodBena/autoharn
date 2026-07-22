#!/usr/bin/env python3
"""Seen-red specimen for the contemporaneity-degrade gate (forecloses finding 12). The fix distinguishes
could-not-test (exit 3) from tested-clean (exit 0). This reproduces the pre-fix exit rule — `exit(0)` on
a degrade — and shows it renders an UNREGISTERED (N/A) target with the SAME code as a clean run, so a
manifest keying on the exit code cannot tell them apart (the finding-12 defect). Banked as red.txt."""
from __future__ import annotations


def _prefix_exit_code(errored: bool, na_only: bool, ran_any: bool) -> int:
    """The pre-fix contract: a degrade was NOT given a distinct code — na_only exited 0, same as clean."""
    if errored:
        return 1
    return 0   # <-- the defect: N/A collapses into the clean code


def _fixed_exit_code(errored: bool, na_only: bool, ran_any: bool) -> int:
    return 1 if errored else (3 if (na_only and not ran_any) else 0)


def main() -> int:
    # the N/A case: nothing analyzable (na_only, nothing ran)
    na = dict(errored=False, na_only=True, ran_any=False)
    clean = dict(errored=False, na_only=False, ran_any=True)
    pre_na, pre_clean = _prefix_exit_code(**na), _prefix_exit_code(**clean)
    fix_na, fix_clean = _fixed_exit_code(**na), _fixed_exit_code(**clean)
    if pre_na != pre_clean:
        print("SPECIMEN INERT — the pre-fix rule already distinguished N/A from clean (unexpected).")
        return 1
    print(f"# contemporaneity-degrade FAIL — pre-fix exit rule: N/A target exits {pre_na}, clean exits "
          f"{pre_clean} — INDISTINGUISHABLE. A manifest reads could-not-test as tested-clean (finding 12). "
          f"(The fixed rule exits N/A={fix_na} vs clean={fix_clean}.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
