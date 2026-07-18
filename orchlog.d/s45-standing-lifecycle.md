subject: 94f5b7a
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

s45 (`94f5b7a`) landed: a db_role's standing declaration and a principal's suspension can now
be **reversed**, each through its own attributed, dated act. Before this delta, s40/s41 gave
you a way IN to both states and no sanctioned way OUT — this note exists because that gap was
real and this closes half of it (unbind, lift) while making the other half (revocation) a
kernel-enforced dead end rather than merely an unbuilt verb. Full spec:
[design/FABLE-STANDING-LIFECYCLE-SPEC.md](../design/FABLE-STANDING-LIFECYCLE-SPEC.md) (§0 has
the executive summary).

**Read this before assuming your world has any of it: EXISTING worlds gain NOTHING here.** Runs
are strictly linear — s45 applies only at a *future* world's [birth](../GLOSSARY.md#birth-chain).
A world scaffolded before commit `94f5b7a` keeps its old four-kind `principal_binding_active`
CHECK and its unreversible declarations/suspensions forever; nothing here is retrofitted onto
it. Run `./migrate <deployment-dir> --dry-run` to see whether your world has s45; if it names
it as missing, none of the two new verbs below exist for you until your next real world is
born on a checkout that carries this commit.

**Two new verbs, one tightened one.**

- **`./led principal undeclare-standing [--db-role <role>]`** (NEW) — repoints a db_role's
  standing declaration back to *undeclared*. After an unbind, an anonymous write on that role
  (no `LED_ACTOR`) refuses again, exactly like a role that was never declared for. The unbind
  is forward-only: rows already written under the old declaration stay attributed to the
  outgoing principal forever — if the reason for unbinding was that past rows were
  misattributed, that is the defeat-pipeline's job (below), never a retroactive rewrite here.
- **`./led principal lift-suspension <name>`** (NEW) — reverses a suspension: the named
  principal's writes are accepted again. This does NOT touch revocation — a revoked principal
  stays revoked; `lift-suspension` on a principal that is both suspended and revoked still
  writes the lift (and prints a warning that standing stays `revoked`, because revocation
  dominates), but there is no verb, in this or any prior version, that reverses a revocation.
  **Revocation is now terminal by type, enforced by the kernel itself**: a lift-shaped
  revocation row is unrepresentable (the CHECK the flag lives on simply excludes the
  `principal_revoked` kind), and a kernel-level supersession rule refuses any row that tries
  to hide a revocation behind an unrelated superseding row. The only way back from revocation
  remains what s40/s41 already gave you: register a fresh successor principal and record
  `./led principal relate <new> succeeds <old>`.
- **`./led principal suspend`** gains a duplicate-active guard: attempting to suspend an
  already-suspended principal a second time now refuses (matching the guard every s41 bind
  verb already carries) unless you name the existing suspension with `--supersedes` — a
  rationale-correcting re-suspend, not a second independent suspension.

**One rule worth internalizing before you reach for either new verb: lifecycle standing never
conditions defeat.** Suspending or revoking a principal gates its *future* writes only — it
never withdraws or supersedes anything that principal already wrote, and lifting a suspension
changes nothing about which of that principal's past rows are credited. If a principal's past
work needs discounting, the sanctioned lever is a mismatch attestation under the defeat
pipeline (see
[orchlog.d/defeat-pipeline-and-otel-identity.md](defeat-pipeline-and-otel-identity.md)), never
a lifecycle act. This was a maintainer ruling (ledger row 1481, ratified 2026-07-18), stated
here because a future reader who "notices" a suspended principal's old attestations still
counting is not looking at a bug.

**Every refusal here is a committed, journaled verdict, per the s42/s43 write boundary** (see
[orchlog.d/s42-s43-typed-verdicts.md](s42-s43-typed-verdicts.md)): a write under a still-suspended
or revoked principal, an anonymous write under an unbound role, or an illegal supersession of a
declaration/suspension/revocation each returns a typed `refused` verdict and leaves a readable
`write_refused` row — none of it silently aborts.

**Honest limits, carried forward from the spec's own LIMITS section:**

- A schema owner/superuser can always bypass the triggers this delta adds, same disclosed bound
  as every prior kernel delta.
- The duplicate-active suspension guard is CLI-side; a direct (non-CLI) writer can still stack
  multiple in-force suspensions on one principal, and each then needs its own lift.
- If a world's only active principal is suspended, lifting that suspension needs *another*
  active principal to write it — the lift itself cannot be self-administered. A solo world with
  one principal, once suspended, still needs a schema-owner act to recover; s45 narrows this
  dead-end (a second active principal now suffices where before nothing did) but does not close
  it.

Migration: the usual recipe — end the session, maintainer pulls the checkout, runs `./migrate`
against a *future* world only (never an existing one), restart, `./pickup`.
