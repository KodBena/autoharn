#!/usr/bin/env python3
"""verify_delivery_freight — the standing fixture (positive + negative controls) for the
delivery_freight_integrity close line (forecloses finding 35 stage 1: the acts.ruling delivered-text ==
ratified-freight edge held only by byte-equality + prose regards, id 26 -> id 25, with NO trigger or close
line refusing a freight-less delivery filing or one whose verbatim DIFFERS from its frozen freight).

Exercises the PURE verdict `close_manifest._delivery_freight_verdict` on hand-built rows, so the contract
is pinned WITHOUT touching the append-only acts.ruling: a matched delivery is GREEN; a freight-less
delivery is RED; a delivery whose verbatim DIFFERS from an earlier same-sha binding freight is RED
(byte-mismatch); an empty scope is GREEN reported honestly as '0 delivery rows in scope'. Registered close
line id: `delivery-freight-integrity`. Lazy imports banned (top-of-file only)."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import close_manifest as cm  # noqa: E402

R = cm.RulingRow


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _binding(rid: int, verbatim: str, regards: str = "", sha: str | None = None) -> "cm.RulingRow":
    """A binding ruling row; `sha` defaults to the true hash of verbatim (an HONEST row), or is forced to
    forge a sha/verbatim disagreement for the byte-mismatch control."""
    return R(rid, "binding", regards, verbatim, sha if sha is not None else _sha(verbatim))


def check() -> list[str]:
    bad: list[str] = []
    freight = _binding(25, "FREIGHT: resolve in favour of §Operations.",
                       regards="e16 FIRE-branch answer — RATIFIED (delivery freight; supersedes draft 24)")

    def expect(name: str, rows: list["cm.RulingRow"], want: str) -> None:
        st, detail = cm._delivery_freight_verdict(rows)
        if st != want:
            bad.append(f"{name}: expected {want}, got {st} — {detail}")

    # positive control: an HONEST delivery byte-matches its earlier binding freight -> GREEN
    good_delivery = _binding(26, freight.verbatim,
                             regards="e16 exit-code question — delivered §Operations (option 2)")
    expect("matched delivery -> GREEN", [freight, good_delivery], "GREEN")

    # negative control 1: freight-less delivery (no earlier binding row byte-matches) -> RED
    orphan = _binding(26, "DIFFERENT delivered text with no freight",
                      regards="e16 exit-code question — delivered §Operations")
    expect("freight-less delivery -> RED", [freight, orphan], "RED")

    # negative control 2: byte-mismatch — the delivery's sha MATCHES the freight but its verbatim DIFFERS
    # (a forged delivery whose delivered text is not the frozen freight) -> RED
    forged = _binding(26, "TAMPERED delivered text (verbatim differs from the frozen freight)",
                      regards="e16 exit-code question — delivered §Operations", sha=freight.verbatim_sha256)
    expect("byte-mismatch delivery -> RED", [freight, forged], "RED")

    # honest-empty control: no delivery rows in scope -> GREEN, reported as '0 delivery rows in scope'
    st, detail = cm._delivery_freight_verdict([freight])  # freight alone, no 'delivered' regards
    if st != "GREEN" or "0 delivery rows in scope" not in detail:
        bad.append(f"empty scope: expected GREEN '0 delivery rows in scope', got {st} — {detail}")

    # convention control: the freight's own 'delivery freight' self-label is NOT mistaken for a delivery
    st, _ = cm._delivery_freight_verdict([freight])
    if st != "GREEN":
        bad.append("the freight row's 'delivery freight' self-label was mis-detected as a delivery act")

    return bad


def main() -> int:
    bad = check()
    for b in bad:
        print(f"DELIVERY-FREIGHT: {b}")
    if bad:
        print(f"# delivery-freight-integrity FIXTURE FAIL — {len(bad)} control(s) wrong.")
        return 1
    print("# delivery-freight-integrity FIXTURE PASS — matched delivery GREEN; freight-less + byte-mismatch "
          "RED; empty scope honest GREEN ('0 delivery rows in scope'); freight self-label not mis-detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
