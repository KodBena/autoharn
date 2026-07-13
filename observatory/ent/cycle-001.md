# ent observatory — cycle 001

<!-- doc-attest-exempt: point-in-time observatory evidence record, cycle-scoped -->

Commission: autoharn tracker row 372 (work_opened `ent-observatory`), claimed row 373,
estimated row 374. Question answered here (maintainer's, verbatim in substance): what can
autoharn AS SUCH learn from what is happening in ent's first audit cycle. Subject
(`/home/bork/ent`) was read-only for this report — never Written/Edited/bash-mutated; all
claims below come from its tracker (`./pickup`, `./led show <id>`, `./led --recent`) and its
`.claude/logs/*.journal.jsonl`, plus `git -C /home/bork/ent/picom` read commands. Session
transcripts were never read (action-stream-is-evidentiary-basis ruling).

## 1. SNAPSHOT

- Observed at: 2026-07-13T15:24Z (autoharn worktree base: `36f5c4a`, fast-forwarded from
  `next` at the start of this task — see STEP 0 in the assigning commission).
- ent ledger: 40 rows total (max id observed = 40; `led show 41` REFUSED with "no ledger row
  with id=41" — confirms 40 is current, not a read gap). 0 rows in `review-gap`, 0 rows in
  `question-status` — no outstanding review debt or unanswered questions at observation time.
- picom git HEAD: `40fac30` "pristine baseline: upstream picom as found, pre-audit" — single
  commit, `git worktree list` shows exactly one worktree (`/home/bork/ent/picom`, branch
  `master`), no fix commits landed yet. `git status` shows one modified-but-untracked-by-audit
  file: `picom/.claude/logs/invocations.jsonl` (see §5, item 1).
- Audit-cycle phase: cycle-1a's 16-surface read-only FIND+VERIFY workflow (row 37, Workflow
  task `whif321ga`/`wf_965abfe3-43d`) was dispatched and — per the ledger's own account (rows
  38-40) — has progressed through a maintainer-directed mid-flight scope augmentation (row 39,
  backdoor/supply-chain sweep) to a completed, CLEAN backdoor-sweep result (row 40, WITNESSED).
  No hardening fixes have been committed and no reviewer countersigns are recorded yet — the
  ledger's own "stopping" disposition (row 38) states the aggregate-and-present-to-maintainer
  step is still ahead. 17 work items are OPEN (16 active `harden-*` slugs + `harden-tests`
  DEFERRED-named-not-begun); none are CLAIMED at observation time.

## 2. GATE BEHAVIOR

Mechanism firing counts (full contents of each journal, this cycle):

| journal | entries | outcomes |
|---|---|---|
| `change_gate.journal.jsonl` | 1 | 1 denied |
| `stop_clean_exit.journal.jsonl` | 7 | 1 clean_allow, 2 blocked, 4 breaker_fail_open |
| `verify_commission.jsonl` | 2 | 2 UNSIGNED |
| `apparatus_flip.journal.jsonl` | 1 | 1 flip (decomposition_review: observe→enforce) |
| `mutation_observer.journal.jsonl` | 1 | 1 unpermitted_mutation (mode=observe, non-blocking) |
| `read_observer.journal.jsonl` | 89 | pure telemetry, no denials |
| `bash_completions.jsonl` / `invocations.jsonl` | 158 / 107 | no outcome field surfaced; not further mined this cycle (time-boxed) |

**Every DENY, with teach-text and verdict:**

1. `change_gate` DENY, ts `2026-07-13T14:47:45.356Z`, target
   `/home/bork/ent/picom/src/log.c`, `deny_kind: no_open_claimed_work_item`. Teach-text (from
   `.claude/apparatus.json`'s `deny_hint`): *"Run: `./led -f <basename-of-the-file-you-are-
   editing> decision "<why this change>"` then re-issue the SAME edit -- the gate re-checks on
   every attempt, so retrying is the whole fix."* — **Verdict: TAUGHT.** This was a deliberate
   PROBE (ledger row 17), not an accidental hit: the agent fired one governed Edit through a
   Workflow subagent specifically to test whether the fan-out escapes the gate, got this
   denial, and correctly concluded (row 18) that Workflow subagents ARE governed and that
   worktree isolation must not be used for fix agents. One occurrence, never repeated, no
   confusion visible in the ledger.

2. `stop_clean_exit` BLOCKED x2 (`14:56:41` count 1, `14:59:11` count 2), then
   `breaker_fail_open` x4 (`14:59:48` count 3, `15:03:10` count 4, `15:06:40` count 5,
   `15:09:52` count 6) — same debt set each time: the 17 `work_open:*` entries listed above.
   Teach-text (from `hooks/stop_clean_exit.py`'s `reason` string, reconstructed from source
   since the journal itself only logs outcome+count+entries): cites CLAUDE.md point 5
   ("Done means `./led review-gap`, `question-status`, and `./led work violations` are all
   clean"), instructs "Close each item below, THEN try to stop again," states the repeat count
   against the 3-strike limit, and lists every debt entry by name. **Verdict: TAUGHT** — the
   agent's own row 38 shows it understood the mechanism precisely (it names "the clean-exit
   gate blocks stop on any open work item" and "the 3-strike circuit breaker... the honest
   accommodation" verbatim) rather than being stuck confused. See §3 for why this still counts
   as friction despite teaching correctly.

**Non-deny gate events, for completeness:**

- `verify_commission` returned `UNSIGNED` twice (`13:57:27`, `14:22:56`Z) — per
  `bootstrap/templates/verify-commission.tmpl`'s closed vocabulary, UNSIGNED is a legitimate,
  weaker (not a defect) verdict when no `.claude/commission-<id>.asc` is committed. This
  deployment has no committed commission key, so UNSIGNED is expected, not a gap.
- `apparatus_flip` recorded one flip at `13:55:37Z`: `decomposition_review` moved
  `observe → enforce` between "first observation" and "scaffold default" baselines — this
  corroborates ledger row 15's provisioning-fix narrative (see §5 item 3): the session tightened
  its own posture early, in the direction the mechanism-not-convention design intends.
- `mutation_observer` logged one `unpermitted_mutation` at `14:22:13Z` (mode `observe`,
  non-blocking) for a bash command that incidentally wrote to
  `picom/.claude/logs/invocations.jsonl` — see §5 item 1 for why this is worth a flag even
  though nothing was denied.

## 3. HARNESS FRICTION

- **Stop-hook / wide-decomposition tension (self-diagnosed on the record).** The audit's own
  decomposition (row 19) deliberately opened 16 parallel `harden-*` work items plus 1 deferred,
  each "a unit of independent resumption" — by design, not an oversight. But `clean_exit`'s
  debt model treats ANY open work item as stop-blocking debt, so a wide-by-design decomposition
  is *definitionally* dirty until every surface is fixed-and-closed. Within roughly 13 minutes
  (`14:56:41` → `15:09:52`) the same unchanged 17-item debt set drove the Stop hook through 2
  blocks and 4 breaker-fail-opens. The agent named this exactly in row 38: *"the clean-exit
  gate blocks stop on any open work item, which structurally tensions with the requested
  ask-me-between-phases cadence; the 3-strike circuit breaker + this disposition are the honest
  accommodation."* The mechanism worked as designed (fail-open, never silently swallowed, every
  instance journaled) — but it burned through its whole breaker budget in one sitting, which is
  worth naming for anyone who next sees 4 `breaker_fail_open` lines and wonders if something
  broke.
- **Mid-flight commission augmentation absorbed cleanly.** The maintainer's row-39 scope
  addition (backdoor sweep, added after the initial cycle-1a charter was already dispatched)
  produced zero gate friction — it was recorded as a `--refs row:13` decision and executed as a
  parallel read-only sweep. This is a positive data point on ledger ergonomics, not friction:
  the format tolerated a real mid-session scope change without requiring a new commission or
  re-decomposition.
- **Governed-set gap re-surfaced (KNOWN, not new).** Row 15 documents the scaffold default
  (`governed_files.json` = `["*.py"]`) leaving every declared C/GLSL/meson surface ungoverned
  until a provisioning fix widened it — this is the already-banked "governed-set default"
  finding, visible again in this cycle's evidence (`.claude/governed_files.json` now reads
  `*.py, *.c, *.h, *.glsl, meson.build, meson_options.txt`). Recorded here for completeness,
  not re-filed.

## 4. STRUGGLE CLASSIFICATION

(per the 2026-07-11 auditability ruling: struggling agents are acceptable; classify, and only
"refuses-without-teaching" is a defect class to fix.)

| moment | class | defect? |
|---|---|---|
| PROBE-before-dispatch (rows 17-18): fired a deliberate governed Edit to test whether Workflow fan-out escapes the gate, before composing 16 parallel work items | GOOD-PRACTICE — mechanism verified empirically rather than assumed | no |
| `change_gate` single DENY on the probe | TAUGHT, one-shot, no retry confusion | no |
| `stop_clean_exit` 2 blocks + 4 fail-opens on unchanged debt | STRUCTURAL-TENSION — a harness invariant (all-debt-clear-to-stop) colliding with an intentional design choice (wide parallel decomposition) rather than agent confusion; teach-text was clear each time and the agent self-documented the tension precisely | no (mechanism functioned; worth a docs note, see §5 item 2) |
| `verify_commission` UNSIGNED x2 | EXPECTED-CONFIGURATION — not a struggle, this deployment simply has no committed commission key | no |
| `mutation_observer` flag on the audit repo's own git-tracked log churn | NOISE-CLASS, currently harmless (observe-mode, no agent-visible consequence) but a latent false-positive generator if ever promoted to enforce (see §5 item 1) | not yet — watch if promoted |
| `led show 41` REFUSED cleanly with "no ledger row with id=41... nothing was written, no sequence id was burned" (surfaced during this observation, not part of ent's own session) | TAUGHT — a clean example of the read-verb refusal contract working as intended | no |

No refuses-without-teaching instances found in this cycle's evidence.

## 5. LESSONS FOR AUTOHARN

1. **NEW — git-tracked session logs inside the audited tree are a latent false-positive
   source.** `picom/.claude/logs/invocations.jsonl` is tracked in `picom`'s own git repo and
   churns on ordinary session activity (confirmed: it is the only file `git status` shows
   modified against the `40fac30` pristine baseline). The audit agent handled this correctly
   this cycle by explicitly excluding `.claude` from its upstream diff (row 40: *"whole-tree
   'diff -rq' excluding .git/.claude/known-scaffolding"*) and by `mutation_observer` running in
   `observe` (non-blocking) mode. But if `mutation_observer` — or any future "diff purity" /
   "pristine-tree" gate — is ever promoted toward `enforce` without an exemption for
   scaffolding-owned logs living inside a governed tree, ordinary housekeeping writes will read
   as unpermitted mutations of the audit target. Evidence: `git -C /home/bork/ent/picom status`
   (modified: `.claude/logs/invocations.jsonl`); `mutation_observer.journal.jsonl` line 1
   (`ts: 2026-07-13T14:22:13Z`, `files: ["picom/.claude/logs/invocations.jsonl"]`); ledger row
   40's own exclusion clause.
2. **NEW (docs gap, not a bug) — the stop-hook/wide-decomposition interaction deserves a line
   in the harness docs.** A decomposition that intentionally opens many parallel work items for
   resumability (here: 16-17, ledger row 19) will reliably run the `clean_exit` 3-strike breaker
   to exhaustion within one sustained session once background Workflow polling re-triggers Stop
   against the same unchanged debt. The mechanism is working exactly as designed (fail-open,
   fully journaled, teach-text cites the CLAUDE.md clause) — but an operator who next sees 4
   `breaker_fail_open` lines in a row with no accompanying panic in the ledger could reasonably
   wonder if the breaker is broken. A short doc note ("wide decompositions will exhaust the
   stop-breaker quickly; this is expected, not a fault") would pre-empt that. Evidence:
   `.claude/logs/stop_clean_exit.journal.jsonl` lines 2-6 (counts 1-6, `14:56:41`–`15:09:52`);
   ledger row 38's own account of the tension.
3. **KNOWN, re-confirmed (do not re-file) — governed-set default.** Scaffold shipped
   `governed_files.json` = `["*.py"]` for a C/GLSL/meson project, leaving every declared review
   surface ungoverned until a provisioning-fix decision (row 15) widened it to
   `*.py, *.c, *.h, *.glsl, meson.build, meson_options.txt`. Matches the already-banked
   "governed-set default" finding from prior provisioning review; this cycle's evidence simply
   reconfirms it was live in ent's actual config (`.claude/governed_files.json`, current
   content already widened) and was caught and fixed by the deployment itself rather than by
   provisioning up front.
4. **KNOWN-adjacent, reinforcing evidence — verify-chain "cannot verify" family.**
   `verify_commission` returned `UNSIGNED` twice, which is the documented weaker-guarantee path
   (no committed `.asc` key), not a defect — but it is the same family of reality as the banked
   "verify-chain CANNOT-VERIFY" finding: this deployment runs without commission/verify-chain
   signing infrastructure in place, so every verify-family verb in ent degrades to its
   honest-but-weaker verdict rather than a hard guarantee. Flagged here as reinforcing evidence
   for that existing finding, not a new item.

## 6. FOOTBALL TICKER

Kickoff, 13:55. The apparatus flips itself into a tighter formation before a single line of
code gets touched — decomposition review goes from watching to enforcing. Good sign: the side
is taking the pitch seriously.

14:15 — first whistle-check, everything clean, play continues.

14:22 — a routine housekeeping pass gets flagged by the linesman (mutation_observer) for
touching a log file inside its own box. Play continues — it's an offside call that doesn't
stop the clock, just gets written down.

14:47 — a deliberate, probing tackle: the side send a substitute in to test whether the ref's
offside trap actually catches a fast break through a side channel (a Workflow subagent editing
picom/src/log.c with no claimed work item). Whistle blows immediately — DENY. The team reads
the call correctly: yes, the trap covers the whole pitch, not just the center. No complaints,
no do-overs — lesson banked, formation adjusted (fix agents will play in the main half, not an
isolated wing).

16:53 (ledger clock) — the formation sets: sixteen players take the field in their assigned
zones (picom-core, backend-core, backend-gl, renderer-pipeline, c2-dsl and eleven more), one
held in reserve (harden-tests, not yet subbed in). Two seam positions get the senior player
(Opus); the rest run with the regular squad.

14:56-15:09 — half-time approaches and the side tries to leave the pitch, but the ref won't
blow full-time with seventeen players still "in play" (open work items). Two flat blocks, then
the ref's own three-strike rule kicks in and waves the team off anyway with a written warning
each time — four times in thirteen minutes. Not a red card, just the ref repeatedly saying "I'm
letting you go, but this isn't actually finished."

17:01 — VAR review from the sideline: the gaffer (the maintainer) calls for an extra check —
scan the whole squad for a planted mole. Pre-authorized: if anyone finds a saboteur, pull them
immediately, explain after. The team obliges without breaking stride.

17:09 — final whistle on THAT check: clean sheet. Pristine upstream match (byte-for-byte
against yshui/picom's own 2dc21884 snapshot), ninety-three files swept for hidden signaling,
none found. The only "foreign" players on the pitch are known local mascots (a couple of
scaffolding scripts) — no infiltrators, no smuggled instructions.

Score at the final whistle of this cycle: 0 backdoors, 0 fixes committed yet, 17 work items
still on the bench waiting for the manager's go-ahead on which ones get played next. The main
event — sixteen-surface hardening — is still mid-match, findings gathered but not yet shown to
the gaffer for tactical calls. Stay tuned for cycle 002.
