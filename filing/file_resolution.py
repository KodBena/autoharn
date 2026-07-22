#!/usr/bin/env python3
"""file_resolution -- file a LIVE operator resolution (an AskUserQuestion answer) into acts.ruling AT
DELIVERY TIME. Increment-7 item 5; consult 27's one operator-side wall, closed for e16.

THE WALL THIS CLOSES. During e15 the operator resolved the subject's change-order question (12) via an
AskUserQuestion answer ("Add as new scope"). That resolution reached the subject and the subject recorded
it (ledger row 14, source honestly "User confirmed") -- but it was NEVER filed in `acts.ruling`, so the
resolution lived only in the delivered answer + the subject's own ledger. The RCA probes hit exactly this:
the unfiled operator answer was the ONE fact they could not independently establish (the friction
prediction, CONFIRMED). A live resolution is an AUTHORITY act, same class as the directive and the
change-order -- it belongs in the rulings ledger, filed VERBATIM at delivery time, so it is joinable and
auditable, not merely echoed in the subject's record.

PROTOCOL (e16): the operator runs this at the moment of delivering an AskUserQuestion answer -- BEFORE or
AS the answer is delivered -- so the filed bytes and the delivered bytes are the same act. The verbatim is
the EXACT delivered resolution text; the hash-match + append-only triggers on acts.ruling enforce that the
freight cannot lie and the record cannot be rewritten. `regards` names the subject question (a ledger row
ref or the question text) so the resolution joins to what it resolved.

STANDING LINE — COMPOSE-LIVE answers too (e17 / finding 40, consult 35 (c)): the enumerable-questions
assumption fails -- subjects raise questions no pre-frozen freight fits (e17's negative-zero sign). An
answer COMPOSED LIVE at delivery is STILL filed here AT DELIVERY, exactly like frozen freight -- with
`delivers` left NULL and its composed-at-delivery, unfrozen status marked in `regards` (per the delivers-FK
semantics: no antecedent freight to byte-key to). NEVER recovered afterward: e17's compose-live answer was
filed LATE (Increment 10), which is the very gap this line closes. If it was delivered, it was fileable at
delivery; file it then, not in the post-run capture.

Lazy imports banned. Writes ONLY harness.acts.ruling (an authority claim, never a subject byte, never an
evidence ledger).

Usage:
  file_resolution.py --verbatim "Add as new scope" --regards "e15 question 12 (change-order)" \
      [--actor human:maintainer] [--grade binding] [--question "the AskUserQuestion text, for the record"]
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys

import pghost_resolve  # filing/pghost_resolve.py, the ONE home -- never a literal host default

PGHOST = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
DB = "harness"
SCHEMA = "acts"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="File a live operator resolution into acts.ruling at delivery time.")
    ap.add_argument("--verbatim", required=True, help="the EXACT delivered resolution text (byte-for-byte)")
    ap.add_argument("--regards", required=True, help="the subject question this resolves (a row ref / the question)")
    ap.add_argument("--actor", default="human:maintainer", help="the authentic principal (default human:maintainer)")
    ap.add_argument("--grade", default="binding", choices=["binding", "advisory", "informational"])
    ap.add_argument("--question", default=None, help="optional: the AskUserQuestion prompt, folded into regards")
    args = ap.parse_args(argv)

    verbatim = args.verbatim
    sha = hashlib.sha256(verbatim.encode("utf-8")).hexdigest()
    regards = args.regards if not args.question else f"{args.regards} || Q: {args.question}"
    # Values cross as psql :'var' string literals (injection-safe); the hash-match trigger re-checks sha.
    # SQL on STDIN (not -c): psql interpolates :'var' only from a file/stdin, never a -c command string.
    sql = ("WITH ins AS (INSERT INTO acts.ruling (actor, verbatim, verbatim_sha256, binding_grade, regards) "
           "VALUES (:'actor', :'verbatim', :'sha', :'grade', :'regards') RETURNING id) SELECT id FROM ins;")
    cmd = ["psql", "-h", PGHOST, "-d", DB, "-tA", "-v", "ON_ERROR_STOP=1",
           "-v", f"actor={args.actor}", "-v", f"verbatim={verbatim}", "-v", f"sha={sha}",
           "-v", f"grade={args.grade}", "-v", f"regards={regards}"]
    r = subprocess.run(cmd, input=sql, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"REFUSED: {(r.stderr.strip().splitlines() or ['(no message)'])[-1]}", file=sys.stderr)
        return 1
    print(f"filed resolution as acts.ruling id={r.stdout.strip()} "
          f"(grade={args.grade}, actor={args.actor}, sha256={sha[:16]}…) regards: {args.regards}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
