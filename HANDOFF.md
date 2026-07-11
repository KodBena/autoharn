# HANDOFF (rewritten 2026-07-11 late evening, session e4410ef6 — fresh-context entry point)

This file orients the next orchestrating session (Fable-class if available; otherwise
CLAUDE.md's ORCHESTRATION rules govern who may do what). It condenses and points; it does
not duplicate. The SSOTs it names outrank any summary in it, and every claim below is
re-observable — cite nothing from here without re-checking at the source it names. It
supersedes the prior HANDOFF wholesale (that revision predated this entire day; it
survives in git as commit 9ecc23a).

## Read in this order

0. OPERATING-CARD.md — orientation in one page: the two-cwd model, vocabulary, the six
   operator verbs, start/resume including the signed-commission start, the delta decision
   tree, the hooks map, the verification checklist.
1. CLAUDE.md — law pointers (now five ADRs, including 0017) + ORCHESTRATION. Read the
   named ADRs IN FULL before any work that invokes them.
2. CAPABILITIES.md — the operational truth: 25 witnessed capability items, each with its
   witness or honest UNWITNESSED mark.
3. BACKLOG.md, dated tail from "Run-10 first audit verdict adjudicated (2026-07-11)"
   onward — the live findings, rulings, and dispositions of this day.
4. `git log --oneline -40` — the day's build record is legible commit by commit.

## Where the project stands (2026-07-11, end of day)

Run 11 is LIVE (world `run11`, db `toy` @ 192.168.122.1) and is the first run whose task
entered through the ledger rather than chat: the maintainer signed the commission himself
(`LED_ACTOR=commissioner ./led commission "$(cat ~/aa)"` — row 1, actor=commissioner,
unstamped-but-attributed, which is what FULL signing mode looks like mechanically). Its
world was born on the full current stack: the [birth chain](GLOSSARY.md#birth-chain)
through s25 (the sN tokens number the kernel's schema lineage steps — SSOT
kernel/lineage/README.md; s25 is the latest), six verbs, the ADR-0017 doc gate flipped
to enforce by maintainer instruction.

What this day added, each witnessed (BACKLOG's dated tail carries every disposition):

- **The contemporaneity audit is a live verb with a complete vocabulary.** `./audit`
  joins every ledger row to the invocation that wrote it (via the token lineage step
  s23 stamps onto each row) plus the wall-clock journals, reports per-row
  event-vs-record deltas, and verdicts CONTEMPORANEOUS | BATCHED_DECLARED |
  LATE_DECLARED | BACKFILL_SUSPECT. Lineage step s24 gives writers a declared
  event time (`led --event-time`) so a late entry can be honest the way a paper log's
  marked late entry is; BACKFILL_SUSPECT now means precisely the UNDECLARED gap. Its
  first two live verdicts (run 9's false refusal, run 10's honest intake batch) each
  produced same-day fixes; the run-10 adjudication is the specimen record.
- **ADR-0017 ("The Zero-Context Reader") is ratified law and its enforcement is armed.**
  The maintainer ratified with one proviso (Rule 4 must not prohibit maintainer-initiated
  sweeps — amended at ratification). The A:B:C fresh-context audit loop is the primary
  transport (design/ABC-AUDIT-LOOP-RECIPE.md); the attestation-presence gate blocks
  commits of in-scope .md without a recorded fresh-context read. It has enforced LIVE
  three times, twice escalating at the two-round cap and adjudicated per the recipe.
  BUDGET FOR THIS: editing any maintainer-facing .md now costs a B-fork review cycle.
- **Run 10 closed clean and was audited twice over.** The closure-struggle forensics
  (BACKLOG "Run-10 closure audit") classified five struggles under the maintainer's
  auditability-outranks-ergonomics ruling — the costliest was governance CATCHING a
  premature "done" claim, and only two class-b mechanism gaps produced fixes (both
  landed: `led` kind refusals teach the live vocabulary; the Stop gate journals all four
  outcomes). The Opus retrospective (design/RETROSPECTIVE-RUN10.md) turned the record
  into five process lessons plus six missing record-kinds; the maintainer approved five
  resulting improvements the same evening, all landed: the `./distance-to-clean`
  composed debt view (disaggregated views stay the default — maintainer condition), the
  s25 commission kind with its two signing modes (FULL: the commissioner signs the row
  from his own terminal; LAZY: the implementing agent transcribes the ask verbatim,
  marked as carrying no commissioner guarantee), the read-observer journal (reviewer
  reads now leave traces), intake-granularity judgment guidance, and the
  alternatives-considered convention (no kernel column — filed awaiting witnessed need).
- **Runs are strictly linear** (ruling transcribed in CLAUDE.md; apply-delta.sh is
  deleted, not just demoted). **Hook journals all write UTC-Z.** **The doc-legibility
  toolchain** (link-integrity gate, doc_shapes gate, seeded acronym advisory, per-world
  doc gate via apparatus) landed from the morning's legibility indictment.

## Open work, ranked, with owners

1. **Maintainer decisions, all prepared, none blocking run 11:** (a) review_gap ruling —
   design/REVIEW-GAP-SCOPE-SEMANTICS-RULING.md, one yes/no, recommend YES on option A;
   (b) the two ADR amendment texts drafted 2026-07-10 — held VERBATIM in the previous
   HANDOFF revision (git commit 9ecc23a, open-work item 1(b)); on "ratified", restore
   from there and append, dated, maintainer-attributed; (c) ADR-0009 re-instancing
   yes/no — law/adr/0009-performance-investigation-discipline.md is an unadapted copy
   whose Scope clause still binds the source project's tree; the question is whether to
   re-instance it for autoharn's experiment domain (finding filed in BACKLOG,
   2026-07-10); (d) research-ledger apply — bootstrap/apply-research-ledger.sh, armed, one
   word; (e) pg_hba hardening — design/PG-HBA-HARDENING.md, unchanged; (f) cost/timing
   accounting — designed-unbuilt, waits on his privacy call (ephemera aggregates only);
   (g) OPTIONAL: PGP-signed commissions — stance given 2026-07-11 (narrow yes, at the
   commission seam only), design memo on request.
2. **Run-11 watch duties (live now):** the signed-commission intake is a first — verify
   the agent decomposed FROM row 1, each decomposition row citing it through `--refs`
   (the ledger's typed row-to-row citation field); run `./audit` and
   `./distance-to-clean` against it mid/post-run; classify any closure struggles under
   the standing three-class rubric (BACKLOG "Maintainer priority ruling", 2026-07-11)
   before proposing anything.
3. **Configuration commission (queued behind run-11 quiet time):** CONFIGURATION.md
   (adopter-facing, one page, ADR-0017-compliant), the apparatus unknown-key sweep
   (typo'd mechanism names are silently ignored today — fail-open), the autoharn
   install-path contract statement, and the pg_hba/setup FAQ (maintainer disposed
   provisioning as FAQ-scope, 2026-07-11).
4. **Audit verb completions, filed:** the SQL-floor differential for `./audit` (single
   ASP producer today — not marriage-grade), the `--retain` default question,
   session-level granularity, Part 3 (deontic/temporal preamble program).
   design/CONTEMPORANEITY-AUDIT.md's Status section is the ledger of what is and is not
   built.
5. **Prudential, filed only:** attestation-record adjudication field (seam found at the
   first live escalation); detector Register 1 (design/ARTIFACT-VS-REQUIREMENTS-
   DETECTOR.md); kernel-column candidates (superseded_by, tier, alternatives) all
   awaiting witnessed need; an ASP/SQL consumer for commission rows (named in s25's own
   header).

## Standing cautions (paid for; details in BACKLOG's tail)

- The freeze rule covers hooks/, bootstrap/templates/, AND live-executed engine/ code in
  spirit: a wired session in any run* world means build-new-then-swap, never edit-live.
  Check `pgrep -a claude` + `readlink /proc/<pid>/cwd` at edit time, every time.
- Concurrent agents race the shared git index. The proven pattern: agents work in
  isolated worktrees; the orchestrator integrates in its OWN scratch worktree and lands
  main as one short merge. BACKLOG append-append conflicts resolve keep-both.
- Verify artifacts, never reports — including your own prior claims and your agents'
  summary messages (one witnessed case this day: an agent's message said "ran clean"
  while its banked artifact honestly said "refused"; the artifact was right).
- The maintainer is an executive-level non-expert who reads refusals, not source. Every
  operator step is a verb or it is a defect. Questions to him: prepared, yes/no, ONE
  recommendation, costs named. His standing priority: auditability outranks agent
  ergonomics — ergonomics improvements only with auditability held constant.
- Fable never writes SQL; Sonnet executes; Opus needs firm rails and evidence-pointer
  duties (both Opus engagements this day ran clean under those rails).
