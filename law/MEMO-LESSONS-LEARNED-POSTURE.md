# MEMO — Lessons-Learned Posture: where operational lessons live on the record

- **Status:** Guidance memorandum — an assumed posture with its rationale, maintainer-ratified
  2026-07-26 from a fresh-context consult (a review by an instance given only the primary
  sources and the question, never the working conversation) on the classification question. It is **not** a tenet.
- **Rank:** BELOW the ADRs (the Architecture Decision Records in [`adr/`](adr/)). On any
  conflict between this memo and an ADR, the ADR wins, always. This memo guides day-to-day
  recording choices; it does not legislate.
- **Home:** `law/` deliberately. Files in `law/` are exempt from the documentation-decay and
  vestigial sweeps (the periodic staleness-review and archival-relocation passes most other
  docs are subject to) and change only by maintainer amendment — this posture stays stable
  while the documentation landscape re-orients around it. The precedent for a non-ADR file
  holding this rank here is [`STANDARDS-REGISTRY.md`](STANDARDS-REGISTRY.md).
- **Audience:** this memo is for anyone writing rows to the project's decision ledger (the
  append-only record written and read via `./autoharn led`), and for auditors — the named
  consumer — who enumerate what the project has learned.

## Executive summary

Operational lessons — durable wisdom arising from incidents, near-misses, process faceplants,
and design-shaping observations — get **no ledger kind of their own**. The event enters the
ledger at the moment of contact as a `finding` (or `snag` for an operational obstruction);
a lesson the project **adopts** as standing practice is recorded as a `decision` row that
states the lesson and cites at least one incident row, which places it in the in-force
standing set (`./autoharn led standing`) that survives world succession — a
[world](../GLOSSARY.md#world) being one scaffolded deployment of this harness's database and
apparatus, and succession being the act of retiring one world and scaffolding its successor. Auditors enumerate
lessons via that standing set plus its citation trail. A derived, mechanical `lessons` view is
a named follow-up with named triggers, not built now.

## The posture

**1 — Where lessons enter the record.** An incident, near-miss, faceplant, or design-shaping
observation is written as a `finding` row — or a `snag` row when it is an operational
obstruction — at the moment of contact, with its witness in the row's `evidence` column. These
are true fits of the existing vocabulary: those kinds exist to record exactly what was
observed, where, with what proof. When the project then commits to operating by what the event
taught — the point at which an observation becomes an *adopted lesson* — that adoption is
written as a `decision` row which (a) states the lesson itself as its statement, (b) cites at
least one originating incident row id in its `refs` or `evidence` column (a lesson's claim
carries its witness, like any other claim here), and (c) thereby joins the in-force standing
set returned by `./autoharn led standing` — the set that is re-asserted, row by re-judged row,
into the successor world when one world is retired and the next is scaffolded. This codifies at write time what the rebirth
runbook ([`user-guide/FOSSIL-EXPERIENCE-REBIRTH-RUNBOOK.md`](../user-guide/FOSSIL-EXPERIENCE-REBIRTH-RUNBOOK.md)
§1.12) already rules at succession time: the raw failure record stays behind as read-only
evidence, cite-only; already-extracted lessons cross as standing decisions and procedures.

**2 — Why there is no `lesson` kind.** The ledger's `kind` column types the *act* a row
performs — find, decide, ask, verify, snag, review, and the typed lifecycle events (the
machine-shaped kinds such as `work_opened`, `work_closed`, or `missive_sent`, each recording
one step of a governed process) — while
"lesson learned" names a *genre of content* that legitimately arrives under several acts as it
matures from observation to adopted practice. Admitting a genre into the act vocabulary is the
fabricated-category move [ADR-0008](adr/0008-classification-discipline.md)'s negative register
(its rule against *creating* a category no case honestly fits, the counterpart of its positive
rule against *picking* a near-fit from an existing vocabulary) refuses: a `lesson` kind would be a synthetic near-duplicate straddling `finding` and
`decision`, its boundary ("did this arise from operational experience?") undecidable per row by
the many hands writing this ledger, so misfiled rows would silently leak out of it — and a
register whose completeness an auditor cannot bound is worse than one assembled from verifiable
citations. ADR-0008's own substitution test (name the failure shape in its most general form, list every
surface the same shape could reach, and calibrate to the worst case on that list) seals the
refusal: the failure shape in general form is *genre admitted onto the act axis*, and its
worst case is the kernel's closed,
hash-chained kind vocabulary eroding into a topic folksonomy (an uncontrolled, crowd-grown
tagging scheme), one plausible genre at a time.

**3 — How auditors enumerate, and the named follow-up.** An auditor asking "what has this
project learned, on what evidence, and is it still in force?" runs `./autoharn led standing`
for the adopted lessons, then follows each row's `refs`/`evidence` citations back to the
incident rows (superseded and refuted lessons remain visible in the ledger's history with
their disposition — the record is append-only). The enumeration's completeness is exactly as
good as the citation discipline in paragraph 1, which review can check. If a mechanical
enumerator is ever needed, the committed path is a derived `lessons` view joining in-force
standing decisions to their cited incident rows — an additive, derived-view-only
[kernel lineage](../GLOSSARY.md#birth-chain) delta (a change entering the kernel's append-only
schema-birth chain, `kernel/lineage/`), inside the pre-ratified fail-safe class
([`CLAUDE.md`](../CLAUDE.md)'s class-ratified fail-safe deltas ruling, 2026-07-09) — and
**not** a new kind. Its named triggers, per ADR-0008's scheduled-for-revision exception:
the first real auditor pass that finds manual assembly insufficient, or a citation-discipline
review catching leakage. Until a trigger fires, this memo's convention is the whole mechanism.
