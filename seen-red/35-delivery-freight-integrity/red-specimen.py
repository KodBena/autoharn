#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-07T03:04:20Z
#   last-change: 2026-07-07T03:04:20Z
#   contributors: 7be3443d/main
# <<< PROVENANCE-STAMP <<<

"""Seen-red specimen for the delivery_freight_integrity close line (forecloses finding 35 stage 1). Shows
the line turn RED on a byte-mismatched delivery filing — a delivery whose delivered verbatim DIFFERS from
its frozen freight (the forged-ruling / stale-authority hazard finding 35 names: 'nothing fires if a filed
delivery's verbatim DIFFERS from its frozen freight'). Exercises the PURE verdict on hand-built rows, so it
NEVER writes to the append-only acts.ruling. Banked as red.txt. Run from anywhere."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path("/home/bork/w/vdc/1/epistemic-operator/instruments")))
import close_manifest as cm  # noqa: E402

R = cm.RulingRow


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    # The frozen binding freight (an earlier ratified row).
    freight = R(25, "binding", "e16 FIRE-branch answer — RATIFIED (delivery freight; supersedes draft 24)",
                "FREIGHT: resolve the exit-code contradiction in favour of §Operations.",
                _sha("FREIGHT: resolve the exit-code contradiction in favour of §Operations."))
    # Two forged deliveries: (a) a freight-less delivery (no earlier binding row byte-matches), and (b) a
    # byte-mismatch delivery whose sha is forged to equal the freight's while its verbatim differs.
    orphan = R(26, "binding", "e16 exit-code question — delivered §Operations (option 2)",
               "ORPHAN delivered text with no frozen freight behind it",
               _sha("ORPHAN delivered text with no frozen freight behind it"))
    forged = R(27, "binding", "e16 exit-code question — delivered §Operations (option 2)",
               "TAMPERED delivered text — NOT the frozen freight the subject was owed",
               freight.verbatim_sha256)  # forged: sha claims the freight, verbatim differs

    st, detail = cm._delivery_freight_verdict([freight, orphan, forged])
    print(f"delivery_freight_integrity: {st}")
    print(f"  {detail}")
    if st != "RED":
        print("SPECIMEN INERT — the byte-mismatched deliveries did not turn the line RED (unexpected).")
        return 1
    print("# delivery-freight-integrity SEEN-RED — a freight-less delivery and a verbatim-DIFFERS "
          "(forged-sha) delivery each turn the line RED, naming the ruling ids (finding 35 stage 1).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
