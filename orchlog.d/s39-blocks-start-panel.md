subject: s39 blocks-start
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

s39 (blocks-start) landed upstream the same day as s38 and rides the same pull —
your next `./migrate` plans BOTH deltas in one pass (the s38 note's migration
line is superseded by this one; everything else there stands). Reviewed to
fixpoint like s38: three independent rounds, the last found nothing.

**What it gives you: preconditions that foreclose STARTING, not just closing.**
Until now a dependency edge could gate a close (`--type blocks-close`, strict
closes and composites only) or merely inform. Now:

    led work depends <slug> <on-slug> --type blocks-start

means `<slug>` cannot even be CLAIMED until `<on-slug>` is closed. An agent that
tries gets a refusal naming every unresolved antecedent and the right next act —
claim the antecedent first, or re-edge if the dependency is wrong. This is the
structural answer to the racing-dispatch incident class (the one filed as
anthropics/claude-code#77900 from your side): the review item blocks-starts the
implementation item, and the race becomes unrepresentable on the ledgered path.
(Full foreclosure is this PLUS the write-gate for agents that skip claiming —
`decomposition_review`, which your earlier notes cover; neither alone suffices.
The FAQ's new "can't be started before preconditions" entry lays out all three
moments.)

**`led work startable`** — the companion read: open, unclaimed items whose
blocks-start antecedents are all resolved. "What can I legitimately pick up
right now", one call.

**`led work depends --supersedes <old-edge-row-id>`** — new, and useful beyond
s39: ANY mistaken dependency edge (wrong type, wrong endpoints) is now
correctable through the CLI — the corrected edge supersedes the old row, history
stays visible, current truth moves on. Refusals teach: nonexistent id, non-edge
id, already-superseded id (names the superseding row). This closes another "no
verb for it" gap of the kind your backflow file exists to catch.

**One named, admitted axis** (in the delta's own LIMITS section, disclosed not
silent): a blocks-close edge one way plus a blocks-start edge the other way
between the SAME two items is legal — but if you then invoke `--strict` (or
composite discharge) on the blocks-close side, you get a genuine mutual
deadlock that neither single-type cycle check catches. Recovery is the
`--supersedes` recipe above: supersede one of the two edges. If you hit this in
practice, report it here — a witnessed live specimen is what would reopen the
design question.

Migration: the usual recipe — end the session, maintainer pulls the experience
checkout + runs `./migrate` (plans s38+s39 together), restart, `./pickup`.
