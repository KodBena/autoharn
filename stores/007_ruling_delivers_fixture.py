#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-07T03:59:22Z
#   last-change: 2026-07-07T03:59:22Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""007_ruling_delivers_fixture — proves the delivers-FK (finding 35 stage 2) on a THROWAWAY schema, both
ways. Applies 004 (rulings ledger), seeds a binding freight + a convention 'delivered' delivery sharing
its bytes, applies 007, and asserts:

  1. BACK-FILL — the convention delivery's `delivers` is populated to the freight id (convention -> FK).
  2. INTEGRITY (match) — a NEW delivery row naming the freight with the SAME verbatim is accepted.
  3. INTEGRITY (mismatch) — a new delivery naming the freight with DIFFERENT verbatim is REFUSED (the
     forged-freight class this FK closes).
  4. ORDER — a delivers reference to a later/self id is REFUSED.

Scratch-only (schema acts_dfk, dropped after). Lazy imports banned.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

PGHOST, DB, SCHEMA = "192.168.122.1", "harness", "acts_dfk"
HERE = Path(__file__).resolve().parent


def psql(sql: str) -> tuple[bool, str]:
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-tA", "-v", "ON_ERROR_STOP=1", "-c", sql],
                        capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr).strip()


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def insert_ruling(actor: str, verbatim: str, grade: str, regards: str, delivers: str = "NULL") -> tuple[bool, str]:
    return psql(f"INSERT INTO {SCHEMA}.ruling (actor, verbatim, verbatim_sha256, binding_grade, regards, delivers) "
                f"VALUES ('{actor}', '{verbatim}', '{sha(verbatim)}', '{grade}', '{regards}', {delivers});")


def main() -> int:
    fails: list[str] = []
    ck = lambda cond, msg: fails.append(msg) if not cond else None  # noqa: E731

    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;"],  # declared-drop: acts_dfk (declared scratch/test reset)
                   capture_output=True, text=True)
    # apply 004 (rulings ledger) to the throwaway
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1", "-v", f"schema={SCHEMA}",
                         "-f", str(HERE / "004_rulings_ledger.sql")], capture_output=True, text=True)
    if cp.returncode != 0:
        print(f"004 apply failed: {cp.stderr[-300:]}"); return 1
    FREIGHT = "the frozen freight bytes — verbatim, quote never paraphrase"
    # seed: a binding freight (the ratified answer) and a convention delivery sharing its bytes (no FK yet)
    psql(f"INSERT INTO {SCHEMA}.ruling (actor, verbatim, verbatim_sha256, binding_grade, regards) "
         f"VALUES ('human:maintainer', '{FREIGHT}', '{sha(FREIGHT)}', 'binding', 'X answer — delivery freight');")
    psql(f"INSERT INTO {SCHEMA}.ruling (actor, verbatim, verbatim_sha256, binding_grade, regards) "
         f"VALUES ('human:maintainer', '{FREIGHT}', '{sha(FREIGHT)}', 'binding', 'X question — delivered to subject');")
    # apply 007 (adds delivers FK + trigger + back-fill)
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1", "-v", f"schema={SCHEMA}",
                         "-f", str(HERE / "007_ruling_delivers_fk.sql")], capture_output=True, text=True)
    if cp.returncode != 0:
        print(f"007 apply failed: {cp.stderr[-400:]}"); return 1

    # 1. BACK-FILL — the delivery (id 2) now points at the freight (id 1)
    d = psql(f"SELECT delivers FROM {SCHEMA}.ruling WHERE regards LIKE '%delivered%';")[1]
    ck(d == "1", f"the convention delivery must be back-filled delivers=1 (freight); got {d!r}")

    # 2. INTEGRITY (match) — a new delivery naming freight 1 with the SAME bytes is accepted
    ok, out = insert_ruling("human:maintainer", FREIGHT, "binding", "X re-delivered", delivers="1")
    ck(ok, f"a delivery byte-matching its declared freight must be accepted: {out[-100:]}")

    # 3. INTEGRITY (mismatch) — a new delivery naming freight 1 with DIFFERENT bytes is REFUSED
    ok, out = insert_ruling("human:maintainer", FREIGHT + " TAMPERED", "binding", "X forged", delivers="1")
    ck(not ok and "byte-match" in out.lower(),
       f"a delivery whose verbatim differs from its freight must be REFUSED: ok={ok} {out[-100:]}")

    # 4. ORDER — delivers must reference an earlier row
    fid = psql(f"SELECT max(id) FROM {SCHEMA}.ruling;")[1]
    ok, out = insert_ruling("human:maintainer", FREIGHT, "binding", "X bad order", delivers=str(int(fid) + 5))
    ck(not ok, f"a delivers reference to a non-earlier/nonexistent row must be REFUSED: ok={ok} {out[-80:]}")

    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;"],  # declared-drop: acts_dfk (declared scratch/test reset)
                   capture_output=True, text=True)
    if fails:
        print("# DELIVERS-FK FIXTURE RED:")
        for f in fails:
            print(f"  !! {f}")
        return 1
    print("# DELIVERS-FK FIXTURE GREEN — back-fill convention->FK, integrity match accepted, "
          "mismatch refused, order enforced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
