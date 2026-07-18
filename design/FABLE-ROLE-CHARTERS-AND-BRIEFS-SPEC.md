# Role charters and derived briefs — the assembly wiring for durable roles

<!-- doc-attest-exempt: build-basis spec; attestation rides witnessed delivery -->

**Status: Fable-authored 2026-07-18 (maintainer's word: "Yes, please do", same date),
build basis. Origin: §11 of the archived
[vestigial_documentation/design/ORCH-AGENTIC-PATTERNS.md](../vestigial_documentation/design/ORCH-AGENTIC-PATTERNS.md)
("Ephemeral principals — durable roles, disposable instances"), whose kernel half has
since landed (s40/s41/s45, halt witnessed at ledger row 1661 WC7) and whose assembly
half this spec builds. Composes with the workflow-unit compiler
([design/FABLE-WORKFLOW-UNIT-COMPILER-SPEC.md](FABLE-WORKFLOW-UNIT-COMPILER-SPEC.md),
whose J1 judgment call this replaces) and feeds the TUI commission (ledger row 1656).
Sonnet builds. NO kernel/lineage, law/, or boundary-route-table edits are licensed —
everything here is CLI-side derivation over objects that already exist; a kernel
inbox VIEW is explicitly deferred to ADR-0011 recurrence.**

## The two halves, named once

- **Charter** — the static half: what this role IS. Per-role markdown
  (`roles/<role>/CHARTER.md` in a scaffolded world), carrying responsibilities,
  scope, constraints, in the register a fresh instance reads first. A charter binds
  only when REGISTERED: a `decision` ledger row naming the role's principal, the
  file's repo-relative path, and its sha256 — the ledger is the authority on which
  charter text is in force (a drifting loose file with no registration row is
  UNREGISTERED and the tooling says so). Amendment = a new registration row
  superseding the old (s31 uniform retraction applies; the old row is retracted
  history, the file's dated-append conventions govern its prose like any doc).
- **Brief** — the derived half: what this role FACES right now. Never authored,
  always computed at instantiation time from the world's own views, scoped to the
  role's principal: its in-force decisions (rows where it is the actor), its
  obligation debt (`review_gap` / `work_review_gap` where it is the obliged actor),
  open questions in its concerns, its claimable work (`work_startable` intersected
  with what the TOML/charter assigns it), and its standing (an ACTIVE line normally;
  a suspension is surfaced LOUDLY with the suspending row's teaching — an instance
  must learn it is suspended from its own brief, not from its first refusal).

An instantiation's context is charter + brief, nothing else. Percolation needs no
mechanism: roles communicate by writing typed rows (a decision naming a concern, a
review regarding a target), and the receiving role's next brief picks them up —
information flow is a derived view over shared history, which the kernel already is.

## Deliverables

1. **`tools/role_charter.py`** — `register <role> <path>` (computes the hash itself
   from on-disk bytes, never caller-supplied; writes the registration row via `led`,
   refusing an unregistered principal with teaching), `show <role>` (the in-force
   charter row + whether the file's current bytes still match the registered hash —
   a mismatch is a loud DRIFT warning, not an error), `amend <role> <path>`
   (supersedes). No raw SQL anywhere; `led` is the write surface.
2. **`tools/role_brief.py`** — `brief <role>` prints the derived brief, one clearly
   headed section per source, each section's provenance named (which view, which
   filter). Transport-honest: sections whose views ride the boundary's fourteen
   routes may be served; work-family sections go via `--led` exactly as the compiler
   does (the served `work *` gap stays named, not papered over).
3. **Compiler integration** — the driver's dispatch step hands the phase's agent
   `charter + brief` for its role instead of J1's raw prose default; the TOML's role
   fields map to registered principals via an explicit `--role-map` (refusing, with
   teaching, a mapping to a principal with no registered charter unless
   `--allow-uncharted` is passed — the escape hatch is loud, not silent).
4. **Scaffold**: `bootstrap/new-project.sh` ships an empty `roles/` with a README
   stating the register-before-binding rule (additive scaffold content only; no
   LINEAGE_CHAIN contact).

## Witnesses (both polarities, scratch worlds only, per-claim not umbrella)

- **WB1** register → row lands, `show` matches; edit the file → `show` reports
  DRIFT naming both hashes; `amend` → old registration retracted, new in force.
- **WB2** brief sections each equal their direct view query on the same world
  (per section); a role with nothing pending gets honest empty sections, not
  absence.
- **WB3** an obligation on the role appears in its brief; an independent review
  discharges it; the next brief no longer carries it.
- **WB4** percolation: role A writes a decision naming a concern; role B's next
  brief carries it under the questions/decisions section it belongs to.
- **WB5** compiler wiring: a driven phase's dispatched context contains the
  registered charter text and a fresh brief; `--role-map` to an uncharted
  principal refuses with teaching; `--allow-uncharted` proceeds and says so.
- **WB6** suspension surfaced: suspend the role (s45); its brief leads with the
  suspension and the lift path; lift; the brief returns to ACTIVE.

## Honest limits, stated now

The charter registration row is a convention over `decision` rows, not a kernel
kind — a malformed hand-written registration is caught by `show`'s hash check, not
refused at write time; minting a typed kind is exactly the ADR-0011 conversion this
spec defers until the convention is witnessed recurring. Role proliferation stays
the operator's judgment (§11's own risk note stands). The brief is a read — it
grants nothing; authority remains entirely the kernel's standing/binding facts.
