# FABLE-DESIGN-CURRENCY-ADVISORY-SPEC — an advisory gate for design/* non-actuality drift

<!-- doc-attest-exempt: Fable-authored spec 2026-07-27, maintainer-directed same day
("when a design is fully discharged or superseded, it should automatically raise an
advisory about its possible non-actuality"); the A:B:C loop runs on the build, not the
proposal text. Removal condition: superseded by the build's merge record, or rejection. -->
<!-- design-currency: status=discharged discharged-by=d534466 -->

This document specifies a small advisory mechanism for the `design/` directory: a
machine-readable currency header that design documents adopt when touched, and a gate
that reads those headers and raises advisories — never failures — when a document has
probably stopped being actual (its build merged, a successor replaced it) or when a
live document leans on one that has. It exists because the directory holds 90 documents
whose `Status:` lines are unparseable free prose, and nothing today notices when a
status quietly stops being true.

- **Status:** PROPOSED 2026-07-27 (maintainer direction verbatim on the ledger row for
  this spec; his design caveat carried: "some design documents depend on others").
  (Header corrected 2026-07-28, autoharn3 design-drift-triage sweep, ledger row 90: both
  this line and the `status=in-build` machine header above stood stale — genuinely so by
  this very spec's own vocabulary, since `gates/design_currency.py` shipped and merged
  (`4cbbb8e` + two fix rounds `a7781ce`/`0f5f8e8`, merge commit `d534466`); corrected to
  `status=discharged discharged-by=d534466` per the gate's own rule that a shipped build
  should carry that token. Historical prose below kept verbatim.)
- **The live specimen motivating it:** design/LOGGING-DIRECTION-SURVEY-2026-07-27.md's
  own exempt marker says "Removal condition: superseded by a ratified logging spec that
  cites it" — that condition came TRUE when FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md
  was ratified citing it, and nothing noticed. The gate exists to notice exactly this.

## 1. Named consumers (per the named-consumer test, ADR-0000's 2026-07-22 anecdote)

1. **An agent or orchestrator about to cite a design doc as current authority.** The
   standing rule ([CLAUDE.md](../CLAUDE.md): "design/ archives are history unless a
   current spec cites them") already demands this judgment; today it runs on memory.
   Decision informed: trust the doc, or verify its status first.
2. **The maintainer at pickup**, deciding whether a discharged/superseded doc's markers
   and cross-references deserve scheduled retirement work.

## 2. The currency header (adopted ON TOUCH, never by sweep — the ADR-0017 Rule 4 precedent)

One HTML comment line near the top of a design doc, grammar fixed and closed:

    <!-- design-currency: status=<token> [discharged-by=<commit-sha>]
         [superseded-by=<design-relative-path>] [depends-on=<path>[,<path>...]] -->

Status tokens (closed set; unknown token = advisory, never guess): `proposed`,
`ratified`, `in-build`, `discharged` (built and merged — the doc is now a historical
record of a completed intent), `superseded` (a named successor replaces it),
`rejected`, `evergreen` (recipes, standing references — never dischargeable),
`historical` (point-in-time records: surveys, retrospectives, decision briefs — actual
BY BEING PAST, no drift possible). `discharged` requires `discharged-by`; `superseded`
requires `superseded-by`. The existing free-prose `Status:` lines stay for humans —
this header is the machine's line, beside them, one fact two renderings.

`depends-on` names the docs this one leans on as LIVE direction. A dependency that
becomes `discharged` is SATISFIED (the thing got built — not drift). A dependency that
becomes `superseded` or `rejected` is the drift case the maintainer's own example names
(this spec's sibling, FABLE-DISPATCH-MECHANICS-SPEC.md, depends on
FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md — had the logging spec been superseded mid-build,
the dispatch spec would be leaning on a ghost).

## 3. The gate: `gates/design_currency.py` — ADVISORY polarity

Modeled on `gates/idris_model_freshness.py`: it prints `!! ADVISORY` lines and always
exits 0 at commit time (a `--strict` flag for humans who want exit codes). Checks, each
mechanical, none heuristic:

1. **Discharge verification:** `discharged-by=<sha>` — advisory if the sha is not an
   ancestor of HEAD. `superseded-by=<path>` — advisory if the target does not exist or
   its own status is not a live, historical, or `discharged` token (amended 2026-07-27:
   the build exposed that excluding `discharged` was backwards — a built-and-merged
   successor is stronger confirmation than a merely-ratified one; `rejected` and
   `superseded` successors stay excluded — a successor that was itself rejected leaves
   the predecessor un-superseded in fact, and a superseded successor means the header
   should point at the END of the chain).
2. **Dependency drift:** for every doc with a live status (`proposed`/`ratified`/
   `in-build`), advisory per `depends-on` target whose status is `superseded` or
   `rejected` (with both paths and both statuses in the message).
3. **Stale-currency smell:** a doc whose status is `discharged`/`superseded`/`rejected`
   — or `historical` while carrying a genuinely-resolved `superseded-by`/`discharged-by`
   fact (amended 2026-07-27: the build surfaced that this spec's own live specimen is
   seeded `historical`, so the original three-token letter missed it; the builder made
   the spirit call and this amendment makes the letter match) — but which still carries
   a `doc-attest-exempt` "Removal condition" marker: the condition is due for action
   (the live specimen's exact shape).
4. **Grammar:** malformed header, unknown token, missing required field — advisory
   naming the doc and the grammar line (a refusal that teaches, applied to the header).
5. **Back-catalog honesty, one line, no per-doc noise:** "N of M design docs carry no
   currency header (adopt on touch)". Free-prose Status lines are NEVER parsed — a
   heuristic that guesses wrong manufactures exactly the false certainty this project
   refuses (the two-biases ruling, ledger row 1887's clauses).

## 4. Scope and non-scope

The gate reads `design/*.md` only. It never edits anything, never blocks a commit,
never deletes markers (item 3 surfaces work; a human or commissioned pass does it).
Seeding: the build seeds headers ONLY on the docs this session already touched
(the logging survey and spec, the dispatch-mechanics spec, the s65 spec, this spec) as
worked examples — the other ~85 adopt on touch, forward-only. No ledger integration in
v1 (the ledger already records ratifications/merges; the header is the doc-local cache
of that truth, and item 1 checks it against git, not against the ledger).

## 5. Witness plan

RED: a fabricated doc with status=discharged and a non-ancestor sha → advisory
witnessed; live doc depending on a superseded doc → advisory; malformed header →
teaching advisory; --strict exits nonzero on each. GREEN: the five seeded docs parse
clean; a depends-on edge to a discharged doc raises NOTHING (satisfaction, not drift —
the polarity the maintainer's example turns on); the live specimen (survey doc, seeded
superseded-by pointing at the ratified spec) raises exactly the item-3 advisory; full
gate run over all 90 docs completes with the one back-catalog line and no per-doc noise
for headerless docs; exit 0 at commit polarity.

## 6. Closure statement

Quantification universe, per
[ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) Rule 2(a):
the docs checked are exactly `design/*.md`; the statuses are the closed EIGHT-token set
§2 enumerates (this line originally said "nine", contradicting §2's own enumeration —
the builder caught the inconsistency and implemented the eight; corrected 2026-07-27);
the checks are the enumerated five. Not covered, stated honestly: docs outside design/
(law/ has its own regime; user-guide/ is evergreen by construction); truth of a header
against the LEDGER's record (the header is self-declared — a doc that lies about its
status defeats item 1 only if the lie includes a real ancestor sha; the ledger and
review remain the authority, this gate is the reminder); the back-catalog until touched.

## License

Public Domain (The Unlicense).
