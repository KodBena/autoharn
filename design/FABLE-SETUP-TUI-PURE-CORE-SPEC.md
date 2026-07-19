# Setup TUI — pure decision core, one commit boundary

<!-- doc-attest-exempt: build-basis spec; attestation rides witnessed delivery -->

**Status: Fable-authored 2026-07-19, build basis. Commission: ledger row 1823
point 2 (maintainer, verbatim there), which also reads row 1786's transactionality
commission at its full strength. Extends [FABLE-SETUP-TUI-SPEC.md](FABLE-SETUP-TUI-SPEC.md)
and binds with every sibling spec's screen discipline. SEQUENCING: builds only
after the Textual-shell build (row 1818) merges — same package surface, serial
dispatch per the standing isolation rule.**

## 1. The diagnosis this spec answers

The wizard's current semantics is progressive: each screen performs its acts as
the operator confirms them (birth at Birth, ledger rows at Hydration, keygen at
Signed genesis, a background service at Boundary), threading effect-state between
screens, and its own banner advertises the philosophy: "if this process dies
mid-flow, you can finish by hand from what was printed" (WT4 witnesses exactly
that). The transactionality work delivered per-ACT atomicity and legible residue
— not the nothing-until-done property row 1786 asked for. ADR-0012 P9 states the
governing posture — a computation is a pure function; every effect lives in a
thin imperative shell — but its LETTER is scoped to compiled components, which is
why two successive ADR audits rightly did not flag the wizard against it. Per the
LAW's own reading rule the spirit governs: this spec applies P9's posture in the
interactive-flow register. (Whether ADR-0012 itself gains a dated amendment
lifting P9 the way the 2026-06-20 amendment lifted P7 cross-language→cross-device
is a maintainer-ratified law/ act, proposed separately — this spec does not touch
law/ and stands on the commission alone.)

## 2. Semantics (binding)

1. **Screens are pure deciders.** A screen computes, displays, and collects
   decisions into THE PLAN. No screen performs a world-effect. The only
   inter-screen state is the append-only plan, read-only probe evidence, and the
   operator's answers; no screen observes an effect of a prior screen, because
   until the boundary there are none.
2. **The plan is typed, and it is a reified program** (maintainer clarification,
   ledger row 1825: the side effects are pushed to the boundary via
   continuations — here in its plain operational sense). Each entry carries the
   exact argv or file-write (path + content), its checklist name, its lesson
   line, and its bindings. A value unknowable before execution — a row id parsed
   from a prior entry's output — is a typed hole rendered symbolically
   ("<row-id of step 5>") and resolved only at commit; a hole is a continuation
   of a prior entry's output, represented, never faked (ADR-0000). The shape
   this gives the whole flow: the decision phase is `screens → Plan` (pure), the
   boundary is `Plan → effects` — so "every side effect at the boundary" is a
   property of the construction, not a discipline anyone has to remember.
3. **One commit boundary at the end.** The full plan is rendered (the dry-run
   WOULD-DO table promoted from rehearsal artifact to the flow's centerpiece),
   the operator gives one final confirm, and the boundary executes entries in
   order through the SAME runner choke points — exact argv echoed, real output
   streamed, checklist per entry. Prepared operator acts (the pg_hba apply) keep
   their press-enter-and-re-probe gates, now at commit time; the propaedeutic
   lesson discipline fires at execution, where the real output is.
4. **`--dry-run` unifies.** A dry run is the decision phase without the commit
   act — no longer a flag threaded through every act but the absence of the one
   act that commits. The choke-point `dry_run` plumbing REMAINS as
   defense-in-depth (a second, independent refusal layer), not as the mechanism.
5. **Declared exceptions — the honest envelope, not purity theater**, each named
   at its site:
   - Read-only probes stay live throughout (a rehearsal that fakes its reads is
     a lie — parent spec, unchanged).
   - The REHEARSAL screen is the wizard's Workspace in exactly P9 rule 4's
     shape: a declared, explicitly-scoped effect on a scratch target, performed
     mid-flow because its evidence informs decisions, with witnessed
     zero-residue teardown. It touches nothing the operator keeps.
   - Everything else — keygen, export, signing, birth, hydration, service
     start — moves to the commit phase. The signed-genesis teach-sequence
     survives intact; it plays at commit, where its real outputs are.
6. **The guarantee envelope is stated, in the UI and the FAQ, in capability
   terms.** BEFORE commit: nothing to clean up — kill the process at any point
   and the destination, keyring, and every ledger are untouched (row 1786's
   property, now structural rather than aspirational). DURING commit: per-act
   atomicity (the existing write_file contract), plus a durable commit journal
   in the destination naming which step runs next, so a mid-commit death
   resumes or finishes by hand from the journal. Whole-flow atomicity across
   Postgres + filesystem + GPG + a background process is NOT claimable and is
   not claimed — decide-then-commit shrinks the exposure window from the whole
   session to the commit phase; the envelope says so plainly.
7. **The three effect-dependent displays, re-derived** (the hard cases, named so
   the builder does not rediscover them): the Principals screen shows the
   scaffold's contractual base (author/reviewer/commissioner) from the registry
   that the scaffold itself writes from, not from a born world's views; the
   genesis-row designation is a symbolic binding until commit; the boundary
   health probe runs at commit, post-start (the PREPARED path unchanged).
8. **The purity is gate-checked, not review-policed** (ADR-0011 Rule 1 at the
   strongest feasible surface, from birth rather than after a recurrence): a
   census-registered gate asserts, at the AST level over `tools/setup_tui/`,
   that calls to the three runner choke points (`run_command`,
   `start_background`, `write_file`) appear ONLY in the commit-executor module
   and the rehearsal module's declared exception — a screen that acquires a
   direct effect call fails the gate. The gate carries the standing
   negative self-check (a synthetic violation must fail red).

## 3. What survives unchanged

The `Ui` seam and all its backends (the Textual shell renders this flow better,
not differently — its sidebar becomes the live plan view); the runner choke
points; the checklist vocabulary (WOULD-DO is the pre-commit rendering
everywhere); `--scripted` (the commit confirm is one more scripted answer);
`--start-at` (now strictly safer — every pre-boundary screen is pure). Fixture
contracts: this restructure is the one legitimate place existing fixture
contracts change, because the flow's observable timing changes. Every changed
fixture is itemized in the report with before/after rationale; the census count
never silently drops; WT4's mid-flow-death contract SPLITS into the two stronger
witnesses below.

## 4. Witnesses (WPC; scratch worlds + scratch GNUPGHOME only)

- **WPC1** pre-commit purity, mechanical: full journey to the commit confirm,
  before/after over filesystem, db, keyring, and process table = zero delta;
  decline the commit → still zero.
- **WPC2** the plan is the execution: pre-commit plan rendering vs. commands
  actually executed at commit — argv text-parity, checklist entry per plan row.
- **WPC3** kill during the decision phase → destination untouched (row 1786's
  property, witnessed).
- **WPC4** kill mid-commit → journal names the next step; a re-entry resumes and
  completes; per-act atomicity holds.
- **WPC5** late binding: a symbolic row-id hole renders symbolically pre-commit
  and resolves to the real id at commit, verified via `led show` on the scratch
  world.
- **WPC6** the rehearsal exception is the ONLY mid-flow effect: WPC1's
  before/after brackets prove nothing else moved; rehearsal teardown zero
  residue.
- **WPC7** dry-run parity: a dry run's plan rendering is byte-identical to a
  committed run's pre-commit rendering for the same answers.

## 5. Build conditions

Changes under `tools/setup_tui/` + `seen-red/` + the FAQ seam (the envelope
statement of §2.6 lands in the setup entry). No kernel, law, serving, hooks, or
bootstrap-script edits — if a step cannot be planned-then-committed without one,
STOP and report (escalation shape). Python, top-of-file imports, all gates.
Per-claim witnessing; zero residue. Single builder, worktree isolation, serial
after the Textual-shell merge.
