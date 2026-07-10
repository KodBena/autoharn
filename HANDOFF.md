# HANDOFF (written 2026-07-11, session be693afb — fresh-context entry point)

Audience: the next orchestrating session (Fable-class if available; otherwise the CLAUDE.md
ORCHESTRATION rules govern who may do what). This file orients; it does not duplicate. The
SSOTs it points at outrank any summary in it, and every claim below is re-observable — cite
nothing from here without re-checking (verification checklist: POST-FABLE-OPERATING-BRIEF.md).

## Read in this order

0. OPERATING-CARD.md — orientation in one page (the two-cwd model, vocabulary, the four
   verbs, start/resume, the delta decision tree, the verification checklist). Added
   2026-07-11 after an Opus fresh-context probe stalled on exactly these gaps; it
   condenses, never supersedes — the SSOTs below outrank it.
1. CLAUDE.md — law pointers + ORCHESTRATION (delegation, class-ratified fail-safe deltas,
   self-application ruling, succession). Read the four ADRs it names IN FULL before any work
   that invokes them.
2. CAPABILITIES.md — the operational truth: 23 witnessed capability items, each with its
   witness or honest UNWITNESSED mark, plus "Not yet enforced" and "Honest limits".
3. BACKLOG.md, dated tail from "Run-5 forensics (2026-07-10)" onward — the live findings and
   the run-7 verification entry.
4. `git log --oneline -40` — the build record of 2026-07-09/10 is legible commit by commit.

## Where the project stands

The core loop is CLOSED and witnessed: run 7 (world `run7`, db `toy` @ 192.168.122.1) ran end
to end under the full mechanism set — permit-to-work (no writes without an open+claimed s22
work item), matcherless stamping (27/27 rows stamp_verified), kernel-verified technical
independence on distinct (session, agent) pairs, the clean-exit Stop gate (first live firing,
silent-allow path), and deliverables committed where the ledger says (`7adaf2b` in run7's own
git). Verification record: BACKLOG "Run-7 phase-1 verification (2026-07-10)" + commit cd7fbe2.
Worlds are born complete: `bootstrap/new-project.sh --new-world` applies kernel s15→s22, seeds
the stamp secret, registers author+reviewer principals, writes the governance preamble into
the world's auto-loaded CLAUDE.md, and writes the `.claude/apparatus.json` switchboard
(per-mechanism off/observe/enforce; anything that spends money per invocation defaults OFF —
maintainer ruling; the demurral classifier is the case in point).

Starting a run is exactly:
```
cd /home/bork/w/vdc/1/autoharn
bootstrap/new-project.sh /home/bork/w/vdc/1/runN --new-world runN --db toy --host 192.168.122.1
cd /home/bork/w/vdc/1/runN && claude    # then type the task; nothing is pasted
```

## Run 8 (maintainer-declared intent, 2026-07-11)

Run 8 will test RESUMPTION: stopping a governed session and picking the work back up (the
world-level mechanism is `./pickup` — derived fresh from the ledger, never stored — plus
Claude Code's own session resume). Nobody has witnessed a governed mid-task resume yet. Note:
run 7's phase 2 (HTML terminal renderer + 16-swatch editor + wiring the 16-color experiment)
is still open in the run7 world and is a natural resumption subject.

## Open work, ranked, with owners

1. **Artifact-vs-requirements detector — design memo (Fable-tier judgment; do NOT delegate the
   design).** The one witnessed blind spot: written-only governance steps (assumption filing,
   the reviewer's antecedent audit) were skipped in run 7 with zero trace, and no gate can
   see it (BACKLOG run-7 entry, finding 2; the run-5 implementer's own analysis of the class
   is quoted in the "unflagged assumption" exchange, 2026-07-10). Needs a design pass, not a
   regex. Nothing blocks runs meanwhile.
2. **review_gap scope semantics — draft ruling for the maintainer.** The gap view catches
   every row by the obliged principal, not just the obligated scope; two consecutive runs paid
   a workaround (fail-safe direction, so no urgency). Draft the worked proposal from the two
   witnessed episodes (runs 5 and 7), then a prepared yes/no. Related small fix, Sonnet-sized:
   `led obligate` teach-text so the direction mistake becomes hard to make.
3. **pg_hba superuser hardening — maintainer's five minutes, fully prepared.** The cluster's
   only superuser (`bork`) has NO password and trust rules admit any role from both hosts;
   run 5 witnessed a live superuser bypass. Walkthrough: design/PG-HBA-HARDENING.md
   (PREPARED-UNAPPLIED, lockout guard included). Until applied, role discipline is
   voluntary-but-observed.
4. **Two ADR amendments AWAITING the maintainer's "ratified"** (drafted 2026-07-10, not yet in
   law/ — law is never edited without his word). On his ratification, append verbatim, dated,
   with "maintainer-ratified" attribution:
   - ADR-0000 Revisit #3: "The out-of-frame rationalization-detector named here was minted as
     a mechanism: hooks/demurral_detect.py (observer; PreToolUse on AskUserQuestion + Stop),
     regression-tested against the adversarial corpus instruments/demurral_corpus.jsonl
     (n=121; precision 0.981, recall 0.929 raw / 0.852 at shipped timeout; witness banked in
     seen-red/demurral-detector/). Its costed classifier defaults off per world. Promotion to
     enforcing remains a maintainer act."
   - ADR-0013 Revisit #2: "Rule 3's enforcement surface tightened from review-only toward the
     gate: the justification-as-suspect check now runs mechanically at the two canonical sites
     (the pre-loaded question; the completion claim). It warns; it does not refuse. The Rule's
     admission stands — the faculty it guards is still the faculty that acts — but the
     demurral now leaves a trace the executor did not choose to leave."
5. **Prudential, unwitnessed-need, filed only:** s23 (claim-before-close sunk into the kernel —
   run 7 showed agents using led faithfully, so wrapper-level held; class-ratified when/if
   built), cross-session independence live witness, Stop-gate BLOCK path live witness, and the
   mutation observer's warn path live — all arrive free from future runs; build nothing for
   them.

## Standing cautions (the ones this session paid for; details in POST-FABLE brief + BACKLOG)

- Verify artifacts, never reports — including your own prior claims (this session's "first
  stamped independence" claim was refuted by run 6's ledger: cite-from-memory fails).
- Hooks execute from THIS repo per invocation in every wired world: never edit hooks/ while
  any wired session is live (`pgrep` + `/proc/<pid>/cwd`, checked at edit time, by the
  editor); build-new-then-swap beats wait-and-block.
- Enumeration fails open (three witnessed stamp evasions; one bash-mutation gap): prefer
  unconditional mechanisms and after-the-fact observers over shape-matching.
- Agents park: a "still running / waiting" stop is the known failure — resume with a directive,
  not a question. Concurrent agents race the shared git index: explicit pathspecs +
  CLAUDE_COMMIT_PATHS, never unstage foreign work (one authorship blemish stands in the
  record from exactly this).
- The maintainer is an executive-level non-expert who reads refusals, not source: every
  operator step is a verb or it is a defect (self-application ruling); questions to him are
  prepared yes/no with one recommendation, and never vacuous — check the class-ratification
  rule before asking anything about deltas.
