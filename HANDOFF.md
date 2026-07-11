# HANDOFF (rewritten 2026-07-11 late evening, session e4410ef6 — fresh-context entry point)

This file orients the next orchestrating session (Fable-class — a session run by Fable, the
maintainer's senior AI collaborator persona named throughout this project's law — if
available; otherwise [CLAUDE.md](CLAUDE.md)'s ORCHESTRATION rules govern who may do what). It condenses and
points; it does not duplicate. The [SSOTs](GLOSSARY.md#ssot) (single sources of truth) it
names outrank any summary in it, and every claim below is
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

## Open work

Open work for the autoharn project itself is no longer tracked in this file — it lives in a
standing, Postgres-backed work tracker deployed at the repository root by
[`bootstrap/track-work.sh`](bootstrap/track-work.sh); see
[design/WORK-STATUS-OFFERING.md](design/WORK-STATUS-OFFERING.md) for what that tracker is and
what question it closes (the omega work-status question — this repo's own repeated,
never-shipped attempt to answer "how does a project track its own open work", named and closed
in that document's own opening section). From the autoharn checkout root, run `./pickup` for
the live resume brief (every open item's full spec text) or `./distance-to-clean` for one
command reporting how many review/question/work-item obligations are outstanding; `./led work
list` / `./led work violations` give the disaggregated per-item views.

Each tracked unit is one `work_opened` row — the tracker's append-only ledger event that opens
a work item under a stable slug, per `led work open <slug> <title>`; a "commission" below is
one such item whose title bundles several related sub-tasks (a maintainer-approved unit of
work, not a separate ledger concept) — counted here as ONE item regardless of how many
sub-tasks its title names. By this count, verified live against `./led work list`, the
migrated inventory (as of 2026-07-11) has exactly 10 items in the OPEN state, numbered 1-10
below; a further 3 items were migrated already CLOSED (not counted in the 10) and are listed
separately afterward.

The 10 open items: (1-6) six maintainer decisions each awaiting a yes/no — review_gap scope
ruling (which countersign-obligation semantics apply, see `design/REVIEW-GAP-SCOPE-SEMANTICS-
RULING.md`), two ADR amendment texts (drafted 2026-07-10, awaiting ratification), ADR-0009
re-instancing (whether to adapt `law/adr/0009-performance-investigation-discipline.md` for this
project), research-ledger apply (running `bootstrap/apply-research-ledger.sh`), pg_hba
hardening (per `design/PG-HBA-HARDENING.md`), and PGP-signed commissions (an optional design
memo, stance already given); (7) the configuration commission, bundling `CONFIGURATION.md`
plus three related follow-ups, still queued; (8) the audit-verb completions, bundling the
SQL-floor differential for `./audit` plus three related follow-ups, still queued; (9) the
small-follow-ups commission, bundling six queued items, described in its own `work_opened`
statement as blocked behind "the GPG merge" — the implementation of
[design/GPG-TRUST-LAYER.md](design/GPG-TRUST-LAYER.md), in progress in a concurrent worktree
as of this revision; (10) this offering's own build, currently claimed by this session.

Separately, 3 items were migrated already CLOSED, outside the count above: a 7th
maintainer-decision item, cost/timing accounting, resolution dropped; two others, resolution
superseded and resolution deferred respectively. Each closed item carries its disposition and
its citing `BACKLOG.md` entry in the statement text of its own `work_opened` row, readable via
`./led work list`. This file's "Open work" section is retired
as of this revision; do not repopulate it here — update the tracker instead.

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
