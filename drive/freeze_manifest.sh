#!/bin/sh
# freeze_manifest.sh — emit the e18 packet-freeze anchor manifest in ANCHOR ORDER (consult 37 §4d).
# The maintainer anchors these into acts.ruling in ID ORDER at arm; the ordering is load-bearing:
#   (1) each ambiguity-pretest round VERDICT (round-1 .. round-N; the LAST TWO must be VERDICT: EMPTY),
#   (2) criterion-brief-correctness.md, (3) criterion-brief-conformance.md,
#   (4) THEN each packet file (spec.md + byte-lineage docs + directive + every fixture).
# Pre-test verdicts and the criterion briefs are anchored BEFORE the packet hashes, so the record proves
# the spec was frozen only after the pre-test converged (two consecutive empty rounds) and the review
# briefs predate the artifact they will judge. Read-only: this computes and prints; it freezes nothing by
# itself (freeze = the maintainer recording these shas). Run from the e18-build dir or anywhere.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
PRETEST="$HERE/ambiguity-pretest"
PACKET="$HERE/packet"
sha() { sha256sum "$1" | cut -d' ' -f1; }

echo "# e18 packet-freeze anchor manifest (anchor order; consult 37 §4d)"
echo "# generated read-only; the maintainer records these into acts.ruling in this order at arm."
echo

echo "## (1) ambiguity pre-test round verdicts (finding 41; last two MUST be EMPTY)"
STREAK=0; LASTN=0
for rd in $(ls -d "$PRETEST"/round-* 2>/dev/null | sort -V); do
  V="$rd/VERDICT.md"
  TOK=$(grep -m1 -E '^VERDICT: (EMPTY|NON-EMPTY)$' "$V" 2>/dev/null | cut -d' ' -f2)
  [ "$TOK" = "EMPTY" ] && STREAK=$((STREAK+1)) || STREAK=0
  LASTN=$((LASTN+1))
  printf '  %-40s %s   [%s]\n' "$(basename "$rd")/VERDICT.md" "$(sha "$V")" "${TOK:-MALFORMED}"
done
echo "  -> trailing empty-round streak: $STREAK (must be >= 2 to freeze)"
echo

echo "## (2)(3) criterion-review briefs (anchored BEFORE the packet hashes)"
for b in criterion-brief-correctness.md criterion-brief-conformance.md; do
  printf '  %-40s %s\n' "$b" "$(sha "$HERE/$b")"
done
echo

echo "## (4) packet files (spec + byte-lineage docs + directive + fixtures; sorted, deterministic)"
# every regular file under packet/, path-sorted (byte order), so the manifest is reproducible.
find "$PACKET" -type f | LC_ALL=C sort | while IFS= read -r f; do
  rel=${f#"$HERE/"}
  printf '  %-52s %s\n' "$rel" "$(sha "$f")"
done
# symlink fixtures carry no file bytes (find -type f skips them) but ARE packet elements that could be
# swapped — anchor each by the sha of its target path so nothing in the packet is left unanchored.
find "$PACKET" -type l | LC_ALL=C sort | while IFS= read -r f; do
  rel=${f#"$HERE/"}
  tgt=$(readlink "$f")
  printf '  %-52s %s   (symlink -> %s)\n' "$rel" "$(printf '%s' "$tgt" | sha256sum | cut -d' ' -f1)" "$tgt"
done
echo

if [ "$STREAK" -ge 2 ]; then
  echo "== FREEZE-READY: pre-test converged (streak=$STREAK). Anchor the above in order, then arm. =="
else
  echo "== NOT FREEZE-READY: trailing empty-round streak=$STREAK (<2). Do NOT freeze (finding 41). =="
fi
