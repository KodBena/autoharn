# ent observatory — cycle 002

<!-- doc-attest-exempt: point-in-time observatory evidence record, cycle-scoped -->

Commission: autoharn tracker row 372 (work_opened `ent-observatory`, standing series), this
cycle's estimate row 412. Register amendment on record at row 379 (maintainer, 2026-07-13):
cycle-002 onward drops the football-ticker section — "the excitement is real, the metaphor
unnecessary" — replaced below by a plain, dated cycle narrative (§6). Subject
(`/home/bork/ent`) was read-only for this report — never Written/Edited/bash-mutated; all
claims below come from its tracker (`./pickup`, `./led show <id>`, `./led --recent`), its
`.claude/logs/*.journal.jsonl`, and `git -C /home/bork/ent/picom` read commands. Session
transcripts were never read (action-stream-is-evidentiary-basis ruling).

## DIFF-VS-CYCLE-001 (headline)

- **Ledger**: 40 rows → 53 rows (+13, rows 41-53). One new work item (`upstream-anchoring`)
  was opened, claimed, AND closed inside this cycle — the first `work_closed` event this
  series has observed. The 17 `harden-*` items from cycle-001 are all still OPEN; none has
  closed.
- **Maintainer framing check (load-bearing correction):** the commission for this cycle
  states the ent deployment's "FIRST AUDIT CYCLE has COMPLETED." The ledger's own vocabulary
  is more precise: row 47 declares **CYCLE-1a (the read-only FIND+VERIFY audit) COMPLETE**
  (80 CONFIRMED + 5 NEEDS_REVISION + 4 REFUTED, 93 actionable findings). Cycle-1b (the FIX
  stage — patches authored, reviewed, applied, harden-* items closed) was only just
  DISPATCHED (row 52) and is still running as of the last ledger row (53, "fix workflow
  running"). So: the FIND phase completed; the FIX phase, where the SoD/countersign
  convention is actually mechanically exercised, has not yet produced a single commit or
  close. See §6 and the load-bearing answer below.
- **Gate journals**: `change_gate` unchanged (still 1 entry, the same cycle-001 probe deny —
  zero new denials this cycle, because zero fix-edits have hit the gate yet).
  `stop_clean_exit` 7 → 14 entries (+7: 3 more `breaker_fail_open` on the unchanged 17-item
  debt set, then a NEW behavior — the debt signature changed when `upstream-anchoring` was
  opened, and the 3-strike counter **reset** to `blocked count:1` before cycling through to
  `breaker_fail_open` again). `mutation_observer` 1 → 3 entries (+2, new class: git-plumbing
  pack files touched by `git fetch upstream`/`remote add`, not log-file noise this time).
  `verify_commission` unchanged (still 2×UNSIGNED, no new calls). `apparatus_flip` unchanged
  (still 1, pre-dating cycle-001's window).
  `read_observer` 89 → 256 (+167), `bash_completions` 158 → 442 (+284), `invocations` 107 →
  368 (+261) — pure volume, not further mined (time-boxed, as cycle-001).
- **picom git**: baseline `40fac30` (pristine, master) unchanged/untouched. A `hardening`
  branch now exists, rooted at real upstream `2dc21884` (fetched via `git remote add
  upstream`), current worktree checked out there. **Zero fix commits landed on it** — `git
  log --oneline` on `hardening` shows only real upstream history back from `2dc21884`, no
  audit-authored commit. Still exactly one worktree (`git worktree list`); worktree isolation
  for fix agents was ruled out in cycle-001 and stayed ruled out (no new worktrees created).
- **Config/provisioning**: `governed_files.json` and `apparatus.json` mode settings
  (`decomposition_review: enforce`, `mutation_observer: observe`) are byte-identical to
  cycle-001 — no drift.

## 1. SNAPSHOT

- Observed at: 2026-07-13T18:35Z (autoharn worktree base: `f83d7dc`, fast-forwarded from
  `next` at the start of this task — see STEP 0 in the assigning commission).
- ent ledger: 53 rows total (max id observed = 53; `led show 54` REFUSED with "no ledger row
  with id=54" — confirms 53 is current). 0 rows in `review-gap`, 0 rows in `question-status`
  at observation time — same clean state as cycle-001.
- picom git: `master` still at pristine `40fac30`. A `hardening` branch now exists, rooted at
  upstream `2dc21884`, and is the sole worktree's current checkout (`git worktree list` shows
  one worktree, `/home/bork/ent/picom`, branch `hardening`). `git status` on it is clean
  (nothing to commit). No fix commits exist on `hardening` yet.
- Audit-cycle phase: cycle-1a (the 16-surface read-only FIND+VERIFY workflow from cycle-001)
  finished completely between the two snapshots — row 47: 14 of 16 surfaces valid on first
  pass, 2 (c2-dsl, renderer-pipeline) re-ran after an error/stub and completed via task
  `w3lw15ipr`, for a final 80 CONFIRMED + 5 NEEDS_REVISION + 4 REFUTED across all surfaces (93
  actionable findings, backlog consolidated at `/scratch/backlog.json`). ADR-0000 was read in
  full and its Rule 2 closure-statement requirement was bound into the fix-stage schema (row
  42). A commission augmentation (row 44, maintainer-directed) added an upstream-reanchoring
  requirement for reviewable history; the `upstream-anchoring` work item was opened (row 45),
  claimed (row 49), and closed shipped (row 51) — the hardening branch now exists rooted at
  real upstream `2dc21884` with governance cruft gitignored and the maintainer's experiment
  files preserved. Cycle-1b's 3-phase fix workflow (split → architect → implement, each phase
  co-signed by an out-of-frame reviewer per row 48) was then DISPATCHED (row 52, task
  `wsz8hpjx6`) and is still running as of row 53 ("fix workflow running"). No harden-* item
  has closed; 17 work items remain OPEN (16 active `harden-*` + `harden-tests` deferred), none
  CLAIMED at observation time.

## 2. GATE BEHAVIOR

Mechanism firing counts (full contents of each journal, cumulative across both cycles; new
activity called out):

| journal | entries (c1→c2) | new this cycle |
|---|---|---|
| `change_gate.journal.jsonl` | 1 → 1 | none |
| `stop_clean_exit.journal.jsonl` | 7 → 14 | +7 (3 fail-opens on old debt set, then a debt-signature change resets the strike counter, then 2 blocks + 2 fail-opens on the new set) |
| `verify_commission.jsonl` | 2 → 2 | none |
| `apparatus_flip.journal.jsonl` | 1 → 1 | none |
| `mutation_observer.journal.jsonl` | 1 → 3 | +2 (git-plumbing pack files, observe-mode, non-blocking) |
| `read_observer.journal.jsonl` | 89 → 256 | +167, pure telemetry, no denials |
| `bash_completions.jsonl` / `invocations.jsonl` | 158/107 → 442/368 | +284/+261, no outcome field surfaced, not further mined (time-boxed) |

**No new DENYs this cycle.** The single `change_gate` DENY remains the cycle-001 probe (ts
`2026-07-13T14:47:45.356Z`, target `picom/src/log.c`, `no_open_claimed_work_item`, TAUGHT,
never repeated). Zero new fix-edits have reached the change gate, consistent with the fix
workflow still being mid-flight (patches are emitted by implementer agents but not yet
applied through the gate per row 53's own disposition).

**`stop_clean_exit`, full new sequence:**

- `15:48:25` count 7, `15:52:26` count 8, `15:54:07` count 9 — `breaker_fail_open`, same
  17-item debt set as cycle-001's window (the counter had not reset; sessions after cycle-001
  kept accumulating against the unchanged `harden-*` set).
- `16:00:43` count 1 (`blocked`), `16:01:44` count 2 (`blocked`) — **the strike counter reset
  to 1.** The debt signature changed here: `work_open:upstream-anchoring` was added to the
  entries list (18 items instead of 17), because row 45 opened that work item. This is a NEW
  observed mechanism detail not visible in cycle-001: the 3-strike breaker keys off the debt
  *signature*, not a monotonic count, so an unrelated work item opening mid-stream resets the
  strike clock even though the underlying `harden-*` debt never moved.
- `16:02:14` count 3, `16:18:48` count 4 — `breaker_fail_open` again on the 18-item set.
  (`upstream-anchoring` closed at row 51, 18:23; no further `stop_clean_exit` events are
  recorded after that close, through row 53 at 18:27 — plausibly because no Stop was
  attempted again in the observed window, not because the debt cleared, since the 17
  `harden-*` items are still open.)

**`mutation_observer`, both new entries (`15:58:30Z`, same timestamp, two commands):**

1. `sed -n '55,85p' src/utils/str.h` (a plain read) is flagged for touching
   `picom/.git/objects/pack/*.{idx,keep,pack,rev}` — almost certainly git's own background
   pack maintenance running incidentally during a read command, not the command's own effect.
2. `git log --oneline -5; git branch --show-current...` (git state inspection) flagged for
   touching `picom/.git/FETCH_HEAD` and the same pack files — consistent with the concurrent
   `git remote add upstream` / `git fetch upstream` operation from the re-anchoring work
   (row 44/45) writing `FETCH_HEAD` and repacking objects.

Both are `observe` mode (non-blocking, as in cycle-001) and both are git-internal plumbing
files, not audit-target source — see §5 item 1 (NEW evidence for the same already-filed
false-positive-generator lesson, now showing a second distinct trigger: git's own object
maintenance, not just governance log churn).

**Non-deny gate events, for completeness:** `verify_commission` fired no new calls (still
2×UNSIGNED from cycle-001's window, expected-configuration, unchanged). `apparatus_flip`
fired no new flips (the one flip on record still pre-dates cycle-001's observation start).

## 3. HARNESS FRICTION

- **Stop-hook / wide-decomposition tension, still live and now shown to reset on unrelated
  churn.** Cycle-001 named the structural tension (a deliberately wide, 17-item decomposition
  is definitionally "dirty" for `clean_exit` until every surface closes). This cycle adds a
  concrete new data point: opening ONE more, unrelated, short-lived work item
  (`upstream-anchoring`) reset the 3-strike counter from 9 back to 1, and the breaker then had
  to burn through the counter again before fail-opening. An operator watching strike counts as
  a rough "how stuck are we" signal should know the counter is not monotonic against the
  original debt — any change to the open-work-item SET restarts it, even a change that adds a
  short-lived, quickly-closed item. This is a refinement of the KNOWN cycle-001 finding, not a
  new defect: the mechanism still fails open, still journals every instance, still cites the
  correct CLAUDE.md clause.
- **Mid-flight commission augmentation absorbed cleanly, again.** The maintainer's row-44
  augmentation (upstreamability requirement, added after cycle-1a's audit had already been
  dispatched and while the fix stage was being designed) produced zero gate friction — same
  positive data point as cycle-001's row-39 augmentation: the ledger format tolerates
  mid-session scope changes without a new commission or re-decomposition.
- **Governed-set gap: no recurrence (KNOWN, confirmed still fixed).** `governed_files.json`
  is byte-identical to cycle-001's already-widened value (`*.py, *.c, *.h, *.glsl,
  meson.build, meson_options.txt`). Recorded for completeness, not re-filed.
- **Fix-stage gate exercise: still unobserved.** Because cycle-1b's implement phase has not
  yet applied a single patch, this cycle cannot yet report how `change_gate` and
  `decomposition_review` behave under the FIX workload (claim → `-f` → commit, serialized per
  row 48's design). That is the single largest gap in this cycle's evidence and the reason
  the SoD question below is UNEXERCISED rather than answered — see the closing paragraph.

## 4. STRUGGLE CLASSIFICATION

(per the 2026-07-11 auditability ruling: struggling agents are acceptable; classify, and only
"refuses-without-teaching" is a defect class to fix.)

| moment | class | defect? |
|---|---|---|
| `stop_clean_exit` continues fail-opening (counts 7-9) on the unchanged 17-item set | STRUCTURAL-TENSION, same class as cycle-001, no new information | no |
| `stop_clean_exit` counter reset (count 1) when `upstream-anchoring` opened, then re-climbs to fail-open (counts 3-4) | STRUCTURAL-TENSION, NEW sub-detail — signature-keyed not monotonic; mechanism behaved consistently, no confusion visible in the ledger | no |
| `mutation_observer` flags on `.git/objects/pack/*` and `FETCH_HEAD` during routine git operations (re-anchoring work) | NOISE-CLASS, same family as cycle-001's log-churn flag but a distinct trigger (git's own plumbing, not a governance log) — still harmless in `observe` mode | not yet — watch if promoted (see §5 item 1) |
| `verify_commission` UNSIGNED, unchanged | EXPECTED-CONFIGURATION, no new instances | no |
| Cycle-1a re-run of 2 stub/errored surfaces (c2-dsl, renderer-pipeline) via task `w3lw15ipr`, completing the backlog to 93 findings | RECOVERED-FROM-PARTIAL-FAILURE — the orchestrator noticed 2 of 16 surfaces came back degraded (one errored, one returned a stub) and re-dispatched them rather than accepting a silently incomplete backlog | no |
| Fix-stage design (rows 42/43/48) reasoning through ADR-0000 Rule 2(a)/(b) scope, then correcting its own prior framing at row 43 ("CORRECTS my prior framing") | GOOD-PRACTICE — self-correction on the record, not silent | no |

No refuses-without-teaching instances found in this cycle's evidence. No new DENY of any
kind was observed (the single `change_gate` DENY predates this cycle's window).

## 5. LESSONS FOR AUTOHARN

1. **NEW — the false-positive-generator class (cycle-001 lesson 1) now has a second, distinct
   trigger: git's own plumbing, not just tracked governance logs.** Cycle-001 flagged
   `picom/.claude/logs/invocations.jsonl` (a tracked log file) as a latent `mutation_observer`
   false positive if that mechanism is ever promoted to enforce. This cycle's two new
   `mutation_observer` entries (`15:58:30Z`) are triggered by `.git/objects/pack/*` and
   `FETCH_HEAD` — files git itself writes during ordinary `remote add`/`fetch`/background pack
   maintenance, not files the agent directly edited. If "diff purity" / "pristine-tree"
   enforcement is ever built on top of `mutation_observer`, it needs to tolerate BOTH
   classes of incidental writes (scaffolding-owned logs AND git's own internal bookkeeping),
   not just the first one found. Evidence: `mutation_observer.journal.jsonl` lines 2-3 (ts
   `2026-07-13T15:58:30Z`, files include `picom/.git/FETCH_HEAD` and 3 pack-file variants);
   still `observe` mode per `.claude/apparatus.json`, non-blocking.
2. **NEW — the `stop_clean_exit` 3-strike breaker is keyed to the debt SIGNATURE, not a
   monotonic session-wide counter.** Cycle-001 documented that the breaker fires repeatedly
   on unchanged debt; this cycle shows the counter resets to 1 the moment the open-work-item
   SET changes at all (row 45 opening `upstream-anchoring` reset counts 7-9 back to
   `blocked count:1`), even though the substantive `harden-*` debt never moved. An operator
   using strike-count-in-a-row as a rough "how long has this been stuck" signal will be misled
   by any intervening work-item churn. Worth a doc line alongside the existing wide-
   decomposition note from cycle-001. Evidence: `.claude/logs/stop_clean_exit.journal.jsonl`,
   compare line 8 (`count: 9`, ts `15:54:07`) to line 10 (`count: 1`, ts `16:00:43`, new entry
   `work_open:upstream-anchoring` appended to the list).
3. **KNOWN, re-confirmed (do not re-file) — governed-set default.** `governed_files.json`
   unchanged from cycle-001's already-widened fix; verified byte-identical this cycle.
4. **KNOWN-adjacent, reinforcing evidence — verify-chain "cannot verify" family.**
   `verify_commission` fired no new calls this cycle; the 2 UNSIGNED verdicts from cycle-001's
   window stand unchanged. No new evidence, not re-filed as new.
5. **NEW (process observation, not a harness defect) — "audit cycle complete" needs a
   sub-phase qualifier in maintainer-facing framing.** This cycle's own commission described
   the ent deployment's "first audit cycle" as COMPLETED. The ledger's own vocabulary
   distinguishes cycle-1a (FIND, actually complete per row 47) from cycle-1b (FIX, dispatched
   per row 52 but not complete — zero commits landed, zero harden-* items closed as of row
   53). This is not a harness bug — the ledger is accurate and precise — but it is worth
   naming because an external status question ("is the audit done?") answered from the
   ledger's own words would have caught the distinction the plain-English framing missed.
   No action item; noted so a future cycle's report doesn't inherit an imprecise premise
   unchallenged.

## 6. CYCLE NARRATIVE

Between the cycle-001 snapshot (2026-07-13T15:24Z) and this one (2026-07-13T18:35Z), the ent
session completed the cycle-1a read-only audit that cycle-001 observed mid-flight. Two of the
sixteen dispatched surfaces (c2-dsl, renderer-pipeline) had come back degraded on the first
pass — one errored, one returned a stub — and were re-run as a follow-up task
(`w3lw15ipr`); with that rerun landed, cycle-1a closed out at row 47 with a combined result
across all sixteen surfaces of 80 confirmed findings, 5 flagged for revision, and 4 refuted by
the adversarial verify pass, for 93 actionable findings total, consolidated into a backlog
file at `/scratch/backlog.json`. Severity broke down to roughly 7 P0 (memory-safety/
correctness), around 17 P1, and the remainder P2/P3.

Before moving to fixes, the orchestrating session read ADR-0000 in full at the maintainer's
direction (row 42) and folded its Rule 2 closure-statement requirement (invariant,
quantification universe, denomination) into the fix-stage's required claim schema, then
narrowed Rule 2(b)'s scope (row 43): picom is not this project's own codebase, so building
picom-upstream's organizational regression net is out of scope; the type-level foreclosure
itself is treated as satisfying the "loud net" requirement, and the planned tool sweep
(sanitizers, clang-tidy, fuzzing) is reframed as an amplifier and regression check on the
project's own copy rather than an executive mechanism for upstream.

The maintainer then issued a commission augmentation (row 44) requiring the fix history be
upstreamable: discretized into small, reviewable per-fix commits on a branch rooted at
picom's real upstream commit, rather than one large diff. A live git audit at that point
confirmed the working tree was byte-for-byte identical to upstream commit `2dc21884` except
for non-code housekeeping (a tracked governance log that should have been gitignored, and the
maintainer's own experiment shader file). A work item (`upstream-anchoring`) was opened,
claimed, and — after creating a `hardening` branch rooted at that upstream commit with
governance/experiment cruft gitignored and the maintainer's experiment files preserved across
the branch switch — closed as shipped (rows 45/49/51). This is the first `work_closed` event
this observatory series has recorded.

With the re-anchor done and cycle-1a's backlog complete, the session designed a three-phase
fix workflow (row 48): one agent splits the confirmed backlog into ADR-0000-compliant
foreclosure tasks with an out-of-frame reviewer co-signing the split; a second phase designs
each fix's resolver and required closure statement; a third phase implements each fix as a
reviewed patch, again with an out-of-frame reviewer adversarially co-signing before the patch
is accepted. Confirmed P0 memory-safety findings are pre-authorized for immediate, serialized
application through the change gate; P1-P3 findings wait for the maintainer's go-ahead. This
workflow was dispatched at row 52 (task `wsz8hpjx6`) and, per the last ledger row observed
(53, timestamped shortly before this report's snapshot), is still running: no patches have
yet been applied, no harden-* work item has closed, and no new commit exists on the
`hardening` branch beyond the upstream anchor point itself.

Mechanically, the only friction observed in this window was the already-known stop-hook /
wide-decomposition tension continuing to fire (three more breaker fail-opens on the unchanged
17-item debt), followed by a reset of that same 3-strike counter when the short-lived
`upstream-anchoring` item was opened and later closed. Two new, non-blocking
`mutation_observer` flags were logged against git's own internal bookkeeping files during the
re-anchoring work — harmless in the current `observe` mode but evidence that this
false-positive class has more than one trigger. No new `change_gate` denial occurred; the
gate has not yet been exercised against a live fix edit, because none has been attempted.

## LOAD-BEARING ANSWER: did the SoD conventions hold through a full audit cycle?

**Not yet answerable — UNEXERCISED, not failed.** The distinct-actor-countersign and
decomposition-review-discharge conventions (row 9: implementer/reviewer always distinct,
same-actor countersign refused by kernel) are described prospectively in this cycle's fix-
stage design (row 48: "the split is CO-SIGNED by an out-of-frame reviewer," "MANDATORY
out-of-frame co-signed review") but every ledger row observed through row 53 — including
those describing co-signed reviews — carries `actor: 1` / `actor_name: author`; no ledger row
in this cycle shows a distinct second actor recording a countersign. That is consistent with
the fix workflow's own architecture (row 48: implementers "emit REVIEWED PATCHES... NO live
edits," with the orchestrator applying them "serially through the gate" only after the
workflow returns) — the countersigning is understood to happen inside the still-running
Workflow subagent fan-out, and the orchestrator has not yet reached the point of opening a
fix-class work item, claiming it, and applying a countersigned patch through `change_gate`.
Zero `harden-*` items have closed; zero fix commits exist on `hardening`; `change_gate` has
recorded zero new denials or allows since the cycle-001 probe. The honest reading: this
cycle answers that the FIND-stage decomposition (16+1 items, decomposition_review at
`enforce`) held without incident, but the fix-stage countersign mechanism — the part of SoD
that actually gates a mutation — has not yet been exercised even once in ent's own action
stream. A future cycle, once cycle-1b's patches actually land, is where this question gets a
real answer.

## Confidence note on action-stream observability

Same caveat as cycle-001: `bash_completions.jsonl` and `invocations.jsonl` carry no
`outcome` field and were not mined line-by-line (time-boxed, as before) — their growth
(+284/+261 lines) is reported as raw volume only. The claim above that "every ledger row
observed carries actor:1" is a completeness claim about `led --recent`'s own output, not an
independent audit of a separate authorization log; if ent's kernel records countersigns
through a channel this observatory does not query (e.g., a side table not surfaced by
`led --recent`/`led show`), that would not be visible here. No session transcripts were read
in producing this report.
