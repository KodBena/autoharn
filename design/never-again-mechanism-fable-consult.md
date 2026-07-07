# Never-again mechanism — blind Fable consult (agent a61e3fef1dd931668, 2026-07-07)

Brief: facts + need only; NO prior shape (neither the maintainer's nor main-loop Fable's);
no filesystem/DB access. Verbatim final message follows.

---

## Core design: the foreclosure debt ledger

The system already has exactly two places where nothing can be silently skipped: DB triggers (fire on every insert) and the close manifest (every registered line renders, N/A is loud, close cannot read complete without all lines). The mechanism lives entirely inside those two choke points. It adds one table, one view, two permanent manifest lines, and one banking convention. It does not touch existing disposition semantics.

**Principle.** A `fixed` disposition closes the *instance*. Under ADR-0000 it simultaneously opens a *class debt*: the obligation to answer "what forecloses the class?" That debt becomes a row-shaped fact the moment the fix is recorded — nobody creates it, a trigger does — and the close gate goes RED while it is unpaid. The "never again" step stops being something a person remembers and becomes something the experiment cannot close around.

**Schema** (append-only like everything else, same trigger conventions):

    CREATE TABLE harness.class_foreclosure (
        foreclosure_id   bigserial PRIMARY KEY,
        finding_id       bigint NOT NULL REFERENCES harness.finding,
        actor            text   NOT NULL,
        kind             text   NOT NULL CHECK (kind IN ('gate','lint','fixture','trigger','waived')),
        check_line_id    text,   -- id of a line registered in the close-manifest / lint-runner registry
        red_artifact     text,   -- repo path of the banked seen-red artifact (ADR-0011)
        red_sha256       text,
        ruling_ref       text,   -- required iff kind = 'waived'
        created_at       timestamptz NOT NULL DEFAULT now()
    );

Trigger-enforced, mirroring the existing waived-requires-ruling pattern: kinds gate|lint|fixture|trigger require all three of check_line_id, red_artifact, red_sha256 non-null; kind waived requires ruling_ref. A foreclosure without a banked SEEN-RED artifact is unrecordable by construction — ADR-0011 is in the schema, not in anyone's discipline.

**Debt definition** — a view, not a process:

    CREATE VIEW harness.foreclosure_debt AS
    SELECT f.finding_id
    FROM harness.finding f
    JOIN harness.finding_disposition d USING (finding_id)   -- terminal disposition = 'fixed'
    LEFT JOIN harness.class_foreclosure c USING (finding_id)
    WHERE d.kind = 'fixed' AND c.foreclosure_id IS NULL;

`explained` owes nothing (not a defect). `waived` is already ruled on. `duplicate-of` rides the canonical finding's foreclosure. `filed` owes nothing until it is eventually fixed — at which point the debt attaches automatically. This also retires the hand-written BACKLOG.md reminders for this class: the debt view *is* the backlog, and it cannot go stale because it is derived, not maintained.

**Two permanent close-manifest lines** (registered once, then run on every close forever — the manifest's existing loudness guarantees they cannot silently not-run):

1. `foreclosure-debt` — RED if harness.foreclosure_debt is nonempty. The experiment cannot close with an unanswered ADR-0000 question.
2. `foreclosure-integrity` — for every non-waived foreclosure row: (a) check_line_id exists in the current manifest/lint registry, and (b) the file at red_artifact exists and matches red_sha256. This catches *rot*: a foreclosure whose gate was later deleted, or whose seen-red evidence drifted, reverts to RED instead of silently decaying into a checkbox.

**Banking convention.** Seen-red artifacts live at docs/adr-evidence/seen-red/<finding_id>-<slug>/, committed, checksummed — composing with the existing ephemera-persistence norm.

**One named pattern, not enforced but documented next to the schema:** specimens 1–3 are all the same shape — a hand-copy drifting from a source of truth — and their foreclosure shape is always *registry + conformance line*, with ledger_target.py as the existing model. Writing this down matters because the mechanism forces foreclosures to exist but cannot force them to be well-shaped; giving the dominant class a canonical shape lowers the cost of doing it right.

## The five specimens under this mechanism

Each becomes a finding row (already the norm), gets `fixed`, and thereby accrues a debt row that blocks close until a registered, seen-red gate exists. The concrete foreclosures each would plausibly force:

1. **Typo'd host octet.** Foreclosure: a lint line `no-literal-ledger-coordinates` — no literal host/db/schema/role strings outside ledger_target.py; arming scripts must import from the registry. Seen-red: a banked fixture script containing a literal IP that the lint flags. The class (any future hand-copied coordinate, not just this octet) dies.
2. **Forgotten DDL apply.** Foreclosure: a `schema-conformance` line — reads ledger_target.py, connects, diffs information_schema against the DDL's expected object set; registered both as an arming postcondition and a close-manifest line. Seen-red: run against a database with one table dropped. "Created the database but forgot the schema" becomes undetectable-for-minutes instead of undetectable-until-downstream.
3. **Dropped mandate paragraph.** Foreclosure: a packet clause registry (same pattern as ledger_target.py — stable clause IDs plus checksums for load-bearing paragraphs) and a `packet-conformance` line verifying every required clause is present in the built packet. Seen-red: a banked packet with the mandate paragraph deleted. Rebuilds can no longer silently shed obligations.
4. **"Task" vs "Agent" adapter gap.** Two-part foreclosure: the adapter hard-fails loudly on an unrecognized tool name (silence never reads as pass), and a fixture-freshness rule — parser stub fixtures are excerpts of real current transcripts, banked with checksums, not hand-typed. Seen-red: a fixture carrying a novel tool name that the adapter rejects loudly.
5. **DROP SCHEMA CASCADE collateral.** Foreclosure: a `destructive-ddl-guard` lint — DROP ... CASCADE banned outside a designated migration path, and reset scripts must declare their target objects, with the instrument refusing a blast radius wider than declared. Seen-red: a banked script containing an undeclared CASCADE that the lint flags.

And the mechanism is its own sixth specimen's foreclosure: the failure "the ADR-0000 conversion was forgotten" is itself a lapse of the omission class, and it is the one the debt view forecloses directly. That is the ADR-0000 answer at the meta level.

## What it deliberately does not do

- **It does not design the gates.** Humans or agents still answer the class question; the mechanism only makes the debt undeniable and the discharge evidence-backed. Automating gate synthesis would produce checkbox gates at scale.
- **It does not classify findings.** No "is this lapse-class?" judgment call or classifier — every `fixed` finding owes a foreclosure by default, with a cheap-but-recorded waiver path (kind='waived' + ruling, the pattern already enforced elsewhere). A classifier would be a new silent-failure surface.
- **It does not judge gate quality.** A narrow, letter-only gate with a genuine seen-red artifact satisfies it. Quality stays with the existing adversarial review pass (harness.rationalization_finding is the right home for "this foreclosure is motivated-reasoning-shaped").
- **It does not block mid-run work or retro-scan history.** Enforcement is at close only, consistent with the existing OPEN-findings gate; old findings can be back-filled or waived by ruling, not forced.
- **It does not duplicate any store.** One table, one view, two manifest lines; findings, dispositions, the manifest instrument, and the registry pattern are all reused as-is.

## Its own failure modes, stated plainly

- **Observation gap.** It forecloses the *conversion* lapse, not the *filing* lapse: a hazard nobody files never enters the ledger. Out of scope by design, and worth saying so no one believes otherwise.
- **Checkbox foreclosures (Goodhart).** A gate matching exactly 192.168.192.1 discharges the debt legally while foreclosing nothing. Seen-red requirements raise the floor but cannot enforce spirit. Mitigation is the existing adversarial pass sampling foreclosure rows; residual risk remains and is the largest one.
- **Waiver inflation.** Everything could be waived. Waivers are rows, so the rate is queryable and visible at close, but the mechanism deliberately does not cap them — that is the maintainer's judgment, kept human.
- **Perverse filing incentive.** "If I file it, I must foreclose it before close" could discourage filing. The counterweights are the cheap recorded waiver and, if needed, a standing maintainer ruling for trivial categories. Worth watching in practice.
- **Gate-body drift.** foreclosure-integrity catches a deleted check line and a drifted seen-red artifact, but not a gate whose registered line still exists while its body was gutted. Pinning gate-body checksums would fix this at the cost of churn on every legitimate edit; I judged that tradeoff not worth it, but it is a real residual, and re-banking a fresh seen-red artifact whenever a gate is substantially edited is the honest manual counterpart.
- **Debt-at-close pressure.** A close deadline plus outstanding debt invites rushed gates. The waiver path is the pressure valve; if waivers spike near closes, that pattern is itself queryable evidence.

The load-bearing property, summarized: every obligation the mechanism creates is either a trigger (cannot be skipped) or a registered manifest line (cannot be silent), and every discharge requires committed seen-red evidence (cannot be vacuous by mere assertion). Nothing in it needs to be remembered.
