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

The core loop is CLOSED and witnessed: run 7 ([world](GLOSSARY.md#world) `run7`, db `toy` @
192.168.122.1) ran end to end under the full mechanism set —
[permit-to-work](GLOSSARY.md#permit-to-work) (no writes without an open+claimed s22
work item), matcherless [stamping](GLOSSARY.md#stamp) (27/27 rows stamp_verified),
kernel-verified technical independence on distinct (session, agent) pairs, the clean-exit
Stop gate (first live firing, silent-allow path), and deliverables committed where the
ledger says (`7adaf2b` in run7's own git). Verification record: BACKLOG "Run-7 phase-1
verification (2026-07-10)" + commit cd7fbe2. Worlds are born complete:
`bootstrap/new-project.sh --new-world` applies kernel s15→s22, seeds the stamp secret,
registers author+reviewer [principals](GLOSSARY.md#principal), writes the governance
preamble into the world's auto-loaded CLAUDE.md, and writes the `.claude/apparatus.json`
switchboard (per-mechanism off/observe/enforce; anything that spends money per invocation
defaults OFF — maintainer ruling; the demurral classifier is the case in point).

Starting a run is exactly:
```
cd /home/bork/w/vdc/1/autoharn
bootstrap/new-project.sh /home/bork/w/vdc/1/runN --new-world runN --db toy --host 192.168.122.1
cd /home/bork/w/vdc/1/runN && claude    # then type the task; nothing is pasted
```

## Run 8 — DONE and verified (2026-07-11); the night-shift record is BACKLOG's dated tail

Run 8 tested resumption (fresh session, ledger hydration — never `--continue`; maintainer
doctrine). Result: hydration FAILED for a reason upstream of pickup — the commission was
never ledgered (run 7 decomposed only what it was about to do), the agent did unledgered
archaeology, recovered the spec, then ran the full discipline cleanly (all claims
verified; Stop-gate BLOCK path live-witnessed; cross-session stamping live-witnessed).
Every finding is filed in BACKLOG 2026-07-11 entries and each got its mechanism the same
night: full-commission intake + investigation/stop-disposition preamble points (1/7/8),
their observer hooks, pickup SPEC blocks, the LED_ACTOR fix, s23 invocation tokens, live
verbs, judge-red-on-violations, `led work asof`, the flag-in-statement tripwire. Also
that night: runs-are-linear ruling (no live worlds, apply-delta demoted), the
contemporaneity indictment (batching systemic; I1 downgraded in the conformance map),
OPERATING-CARD + glossary operating vocabulary, research/LOGIC-COVERAGE-STATUS.md. Note:
run 7's phase 2 (HTML terminal renderer + 16-swatch editor + wiring the 16-color experiment)
is still open in the run7 world and is a natural resumption subject.

## Open work, ranked, with owners (rewritten 2026-07-11 night shift)

1. **Maintainer's morning batch (all prepared, one sitting):** (a) review_gap ruling —
   design/REVIEW-GAP-SCOPE-SEMANTICS-RULING.md, one yes/no, recommend YES on option A;
   (b) the two ADR amendments drafted 2026-07-10; on "ratified", append verbatim, dated,
   maintainer-attributed:
   - ADR-0000 Revisit #3: "The out-of-frame rationalization-detector named here was minted
     as a mechanism: hooks/demurral_detect.py (observer; PreToolUse on AskUserQuestion +
     Stop), regression-tested against the adversarial corpus
     instruments/demurral_corpus.jsonl (n=121; precision 0.981, recall 0.929 raw / 0.852
     at shipped timeout; witness banked in seen-red/demurral-detector/). Its costed
     classifier defaults off per world. Promotion to enforcing remains a maintainer act."
   - ADR-0013 Revisit #2: "Rule 3's enforcement surface tightened from review-only toward
     the gate: the justification-as-suspect check now runs mechanically at the two
     canonical sites (the pre-loaded question; the completion claim). It warns; it does
     not refuse. The Rule's admission stands — the faculty it guards is still the faculty
     that acts — but the demurral now leaves a trace the executor did not choose to
     leave."; (c) ADR-0009 is an UNADAPTED chocofarm copy
   (Scope still binds chocofarm/) — re-instance for autoharn's experiment domain? yes/no,
   amendment drafts on yes; (d) research-ledger apply — one scripted command, armed
   (BACKLOG chocofarm disposition); (e) pg_hba superuser hardening — five minutes,
   design/PG-HBA-HARDENING.md, PREPARED-UNAPPLIED, unchanged.
2. **Audit verb (contemporaneity Part 2)** — design/CONTEMPORANEITY-AUDIT.md, spec'd
   including the binding ASP-first directive; s23 tokens + invocation journal landed and
   inert until this consumes them. Thresholds from the measured runs-5-8 corpus, never
   guessed. The deductive-engine showcase; Part 3 (preamble ordering obligations as one
   deontic/temporal ASP program) sketched behind it.
3. **Artifact-vs-requirements detector Register 1** — design/ARTIFACT-VS-REQUIREMENTS-
   DETECTOR.md; the parked attachment question can now be decided on run-8 evidence
   (14 organic assumption rows, statement-prefix practice, refs edges underused).
4. **Run 9 intent — unset (maintainer's call).** Natural shape: first run under the full
   night-shift mechanism set (live verbs, SPEC-carrying pickup, stop-disposition +
   delegation observers, s23 tokens) with its experiment banked in the research ledger if
   (1d) is applied.
5. **Prudential, filed only:** kernel-column candidates superseded_by + tier (omega
   disposition — await witnessed need); scope tagging + JSON schema (need design); s23-as-
   claim-before-close (unchanged); circuit-breaker 3/3 live witness (arrives free).

## Standing cautions (the ones this session paid for; details in POST-FABLE brief + BACKLOG)

- Verify artifacts, never reports — including your own prior claims (this session's "first
  stamped independence" claim was refuted by run 6's ledger: cite-from-memory fails).
- Hooks AND the operator verbs execute from THIS repo per invocation in every wired world
  (live-verbs refactor, 2026-07-11: worlds carry 3-line shims): never edit hooks/ OR
  bootstrap/templates/ while any wired session is live (`pgrep` + `/proc/<pid>/cwd`,
  checked at edit time, by the editor); build-new-then-swap beats wait-and-block.
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
