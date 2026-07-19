# Setup TUI — principals & authority: the constitutive screen

<!-- doc-attest-exempt: build-basis spec; attestation rides witnessed delivery -->

**Status: Fable-authored 2026-07-19, build basis. Commission: ledger row 1727
(maintainer, verbatim there). Extends [FABLE-SETUP-TUI-SPEC.md](FABLE-SETUP-TUI-SPEC.md)
(posture rules, out-of-sequence and `--dry-run` amendments bind) and sits with
[FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md](FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md)
in the flow. The commission's stated value is PROPAEDEUTIC as much as functional:
the maintainer wants "the rhythm of defining roles and building flexible and
constitutive workflows," against a barrier to entry he names as too high — so
every act on this screen is also a lesson, and the lesson discipline (§2) is a
requirement, not decoration.**

## 1. Placement and scope

**New screen between Birth and Signed genesis** (so the genesis bequeathal can
name authority that was just constituted). Facts line first (feature_facts
entry: aspiration = NIST SP 800-63's identity/lifecycle/binding decomposition
via the s40/s41 family, cited to FABLE-PRINCIPAL-IDENTITY-SPEC; external =
none). ON by default like the genesis screen (same benign-and-skippable test:
every world already receives author/reviewer/commissioner from the scaffold, so
skipping leaves a complete world; one recorded keypress declines).

Offered acts, all driving existing `led` verbs (rule 1 — the TUI never touches
SQL; the kernel's own refusals are the validation of last resort and their
teach-text is RENDERED, never swallowed):

1. **Register principals** — name, class, stated purpose, via
   `led register-principal`. The class choices OFFERED are derived from the
   kernel's own accepted vocabulary (the builder reads s40's CHECK and mirrors
   it; if the verb accepts free text, the screen still offers the kernel's
   list and lets the kernel refuse anything else, rendering its teaching).
   The screen first SHOWS the three principals the scaffold already registered
   (author / reviewer / commissioner, with their classes and purposes read
   from the world's own views) so the operator constitutes on top of a visible
   base, not a mystery.
2. **Authority bindings (s41 vocabulary, worlds at s41+)** — competence grants
   (who is believed competent for what, at what band, on what basis) and typed
   relations (acts-for, dispatched-by, succeeds), each via its `led` verb.
   Each binding form states in one line what the row CONSTITUTES and what it
   does NOT (a competence grant is a recorded belief with a basis, not a
   permission bit; an acts-for relation is representable delegation, not
   enforcement). On a world whose chain lacks s41 the section reports itself
   unavailable with the reason (lineage head shown), never a traceback.
3. **Role charters, trap resolved** — the existing charter registration moves
   behind this screen's flow: chartering a role whose principal is not yet
   registered OFFERS the registration in-flow (one confirm, then the charter
   proceeds) instead of refusing into a dead end. The hydration screen's
   charter item remains for out-of-sequence use but points here.
4. **The workflow on-ramp (pointer, not machinery)** — one closing line
   pointing at the charters-and-briefs and workflow-unit-compiler docs in the
   born world ("roles you define here become the principals your workflow
   units and briefs bind to"), connecting the screen to the "constitutive
   workflows" rhythm the commission names. No workflow authoring in this
   screen's v1.

## 2. The propaedeutic discipline (binding)

Every act on this screen renders, in order: (a) the one-line lesson (what this
row constitutes, in record terms), (b) the EXACT `led` command, (c) the real
streamed output including row id, (d) the checklist entry. An operator who
walks the screen once has seen the full verb vocabulary for constituting
authority, with truthful semantics, and could repeat every act by hand — that
is the propaedeutic claim, and WT-parity (parent spec rule 1) is how it is
kept honest. Lesson lines live in the registries (one home), not inline in
screen code, and say what a thing IS — no marketing, no hedging.

## 3. Dry-run and out-of-sequence

`--dry-run`: no act performed; every prepared registration/grant/charter lands
in the WOULD-DO table with exact argv and the lesson line still shown (the
propaedeutic path works without commitment — arguably its best use). Read-only
displays (the existing-principals table) stay live. `--start-at`: validates
destination, `./led` presence, and lineage-head readability before offering
anything; refuses legibly per precondition.

## 4. Witnesses (scratch worlds only)

- **WP1** full constitutive pass: register a principal (subagent class), grant
  a competence, add one relation, charter the role — all four `led` rows
  verified by id and content via `led show`; checklist accurate per item;
  teardown zero residue.
- **WP2** kernel refusal rendered as teaching: duplicate registration of
  `reviewer` → the s40 loud refusal's teach-text shown on-screen verbatim,
  checklist REFUSED, no traceback. (The kernel is the validator; the TUI's
  added value is legibility.)
- **WP3** the trap, closed: charter for an unregistered role → in-flow
  registration offer → decline leaves a legible REFUSED with the manual
  command; accept completes charter with both row ids echoed.
- **WP4** s41-absent honesty: against a world whose chain stops before s41
  (scratch mid-chain birth, or the cheapest honest equivalent), the bindings
  section reports unavailable-with-reason; nothing offered that would fail.
- **WP5** dry-run: zero acts (mechanical before/after), WOULD-DO rows carry
  argv + lesson lines.
- **WP6** out-of-sequence entry refusals, per precondition, legible.

## 5. Build conditions

Changes under `tools/setup_tui/` + seen-red/ (fixtures census-registered;
smoke fixture extended) + registry entries; no kernel, law, serving, hooks,
bootstrap-script, or `led`-template edits — if a needed `led` verb is missing
or cannot serve a §1 act, STOP and report (escalation shape), never work
around. Python, top-of-file imports; all gates incl. interpreter-boundary lint
(operator-typed names pass the package's closed-alphabet validators BEFORE
argv). Doc seam per row 1699: the FAQ's setup entry gains the screen (or named
deferral). SEQUENCING: builds after the signed-genesis build merges (same
surface; genesis placement depends on this screen's slot). Per-claim
witnessing; zero residue.
