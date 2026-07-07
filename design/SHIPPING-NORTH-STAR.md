# Shipping north star — what "shippable" means for autoharn (Fable, session 7be3443d, 2026-07-07)

Maintainer direction, verbatim core: packaging is "haphazard, and that's the only real
barrier to deployment *as is* for non-institutional actors"; a shippable shape doubles as
"a fixed north star so that the iterationing is consistent." This document is the
DEFINITION — the judgment half, banked while Fable serves. Execution is deliberately
Opus-grade mechanical work against this spec. The definition is stable; the execution
iterates.

## 1. Audience and promise

**Audience:** non-institutional actors — an individual or small team running an AI
collaborator (Claude Code today; the adapter seam keeps it vendor-agnostic) who wants the
epistemic discipline this project built: an append-only decision ledger their collaborator
actually keeps, write-time provenance stamps, refuse-and-teach gates, independent-review
machinery, and a close manifest that refuses to call dishonest work done.
**Constraints inherited from the audience:** self-hosted, zero paid services, one Postgres
instance, one evening to first green close. **The promise (print this on the box):** *your
AI collaborator's record of its work is mechanically checked against what it actually did
— and the checker tells you when it cannot check.*

## 2. The product boundary (the judgment call, made here)

Two repos currently interleave PRODUCT and LAB. Shipping does NOT mean untangling history
or moving the lab — it means a DECLARED boundary:

- **PRODUCT (ships):** kernel DDL lineage (the s17-generation schema: ledger + review_detail
  + stamps + refuse-and-teach triggers + append-only triggers); the stamp hook
  (stamp_intercept.py) + its install story; the instruments (close_manifest + consumers +
  derivers, acts adapter, delivery drill); the filing tools (file_finding, file_foreclosure,
  file_resolution, file_rationalization, staging_guard, persist_claude_ephemera); the
  harness-db DDL (findings, foreclosures, acts.ruling with delivers-FK); pattern docs
  (policy-authoring seam, review-fixpoint protocol, the working-standard CLAUDE.md
  template); GLOSSARY; the BRIEF + BRIEF-CONFORMANCE-MAP (the product's honesty sheet —
  declared exclusions ARE part of the product); a QUICKSTART and ONE worked tutorial.
- **LAB (does not ship, stays public):** experiments (e-series builds, consults, oracles,
  packets), evidence (ephemera, seen-red), BACKLOG, memory apparatus. The lab is the
  product's evidence base and remains linkable — "does not ship" means *not in the install
  path*, never *hidden*.

**Mechanism: a SHIP MANIFEST, not a second home.** `ship/MANIFEST` declares the product
file set (paths in the SSOT repos); a packaging script derives a versioned release
artifact from it. No file is ever copied into a parallel product tree that can drift
(ADR-0012 single-home; the instance-pinned-substrate lesson, finding 36, applied to
packaging). Docs that must read standalone are ASSEMBLED at package time from SSOT
sources, never forked.

## 3. The north star is a GATE, not a slogan

`ship_gate` — a standing close-manifest-style check, run per increment (pre-commit tier
where cheap, close tier where not):

1. **Fresh-bootstrap proof:** on a clean database, the install path (create db → apply
   DDL → install hook → run fixture suite) completes green, scripted end-to-end. The
   quickstart is EXECUTED, not proofread (a quickstart nothing runs is prose — the
   seen-red discipline applied to documentation).
2. **Manifest integrity:** every MANIFEST path exists; no product file imports from a
   lab path (the boundary is checkable, not aspirational); no_lazy_imports green over the
   product set.
3. **Fixture census:** every shipped gate/trigger/line retains its both-polarity fixtures
   and banked seen-red (foreclosure_integrity already checks this for foreclosures;
   extend the census to the shipped set).
4. **Honesty sheet current:** BRIEF-CONFORMANCE-MAP has no silently-open rows (every row
   mechanized / instrumented / declared-exclusion / J-boundary).

"Iterationing is consistent" then has a mechanical meaning: **an increment that breaks
shippability goes RED at its own close.** The north star steers because it gates.

## 4. Versioning and release discipline

Semantic-ish versioning keyed to KERNEL GENERATIONS (s17 → v0.17-line; the kernel lineage
number is already the real compatibility surface). A release = tag + assembled artifact +
its ship_gate output banked + sha256 manifest, anchored in acts.ruling like any freeze.
Releases are cut from green, never patched in place. CHANGELOG derives from increment
trailers (which already exist) — assembled, not hand-written.

## 5. The tutorial (the one new content artifact worth writing)

The e17 arc, sanitized into a worked example: build a small tool under the working
standard; watch the ledger fill; spawn an independent review; see the refuse-and-teach
gate refuse a proxy independence claim; repair honestly; close green. It teaches the
product's entire value proposition in one sitting because it actually happened — and the
lab holds the receipts. (Blind-integrity check before publishing: e17 is closed and its
packet was published-safe by design; verify nothing in the tutorial leaks a FUTURE
experiment's material.)

## 6. Deliberately out of scope for v0

Multi-vendor adapters beyond Claude Code (the seam exists; ship one adapter honestly);
policy pattern library beyond the two designed patterns (ship the seam + design notes,
grow by specimen); the deductive engine (Fable-reserved endpoint — the product ships the
LEDGER it will consume; the engine remains the lab's frontier); any hosted/service form
(self-hosted only); cryptographic hardening of stamps (pre-registered limit, documented
in the honesty sheet, "left to the pros").

## 7. Execution order (Opus-grade; one increment each, roughly)

(i) MANIFEST + boundary lint + packaging script + fresh-bootstrap script; (ii) ship_gate
assembly from existing checks + the fixture census; (iii) QUICKSTART executed-not-
proofread + assembled docs; (iv) the tutorial; (v) first tagged release with banked
ship_gate output. Each lands under the standing increments discipline (staging guard,
seen-red for new gates, trailers, conformance-map updates).
