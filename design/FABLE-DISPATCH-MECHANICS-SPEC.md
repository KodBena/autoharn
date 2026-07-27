# FABLE-DISPATCH-MECHANICS-SPEC — one HTTP-borne identity plumbing for stamps and minted principals

<!-- doc-attest-exempt: Fable-authored spec awaiting maintainer ratification 2026-07-27;
the A:B:C loop runs on the build, not the proposal text. Removal condition: superseded by
the build's merge record, or rejection. -->
<!-- design-currency: status=in-build depends-on=FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md -->

This is a build specification for autoharn's HTTP boundary service (the service that
mediates database writes for the served path). It defines the one mechanism by which
identity — a human operator's vendor stamp, or a dispatched sub-agent's minted principal
— travels from a CLI client, over HTTP, into the same PostgreSQL-level verification the
kernel already performs for a direct `psql` caller. It is aimed at whoever builds or
reviews that service change.

- **Status:** RATIFIED 2026-07-27 (maintainer, same day, after the full +A:B:C loop on
  this text: "let's go; I want the principal stamps done with" — ledger row records it).
  This is [FABLE-PRINCIPAL-STAMPS-SPEC.md](FABLE-PRINCIPAL-STAMPS-SPEC.md)
  §3 item 3 (dispatch mechanics) built out, per the maintainer's standing word on ledger
  row 1471: the confirmed stamp finding "enters the dispatch-mechanics build spec as a
  named requirement — one HTTP-borne identity plumbing serving both minted principals and
  vendor stamps."
- **Basis:** ledger rows 1463/1467 (ledger row — this project's append-only
  decision/audit log, read via `./autoharn led show <id>`; every bare row number in this
  document is one of its entries) (the finding: vendor stamps NEVER reach the served path — `PGOPTIONS` is a
  Postgres client environment variable that sets GUCs (Grand Unified Configuration —
  Postgres's own term for a runtime-settable server parameter) at process launch,
  `_psql()` (`serving/boundary_service.py:845`, the service's one wrapper function
  around every Postgres subprocess invocation) copies the server's own environment; no
  stamped distinctness pair has EVER formed on the real deployment; fail-safe confirmed
  at kernel lineage deltas [`s17`](../s-history.md) (stamp mechanism and independence
  vocabulary) and [`s21`](../kernel/lineage/s21-session-aware-distinctness.sql)
  (session-aware distinctness) — see [s-history.md](../s-history.md) for what each
  numbered delta did), 1468 (deliberately not patched narrowly — no second identity
  mechanism), 1471 (sub-item 4c of that row's ratified defaults — see §3 below — binding
  at THIS build), and the parent spec's §4.1 harness facts and §5 depth witness.
- **Dependency:** the L1 per-request context middleware of
  [FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md](FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md)
  (RATIFIED, in build). Identity parses INTO that context object — it was defined once
  for both consumers by design. This build sequences strictly after that merge.

## 1. The one channel (replaces nothing; fills the witnessed void)

**Client-side:** the CLI (`led.tmpl` via `serving/boundary_cli_client.py`) reads the
identity material already present in its own process environment, and forwards it as
request headers on every boundary call. That material is of two kinds. The first is the
vendor [stamp](../GLOSSARY.md#stamp) (`app.vendor_session`/`app.vendor_hmac`), which the
existing interception convention injects: `hooks/stamp_intercept.py` is the PreToolUse
hook that rewrites every Bash command in a [wired](../GLOSSARY.md#wired) world to carry
those two values as `app.vendor_*` GUCs via `PGOPTIONS`, the HMAC half being a keyed
cryptographic hash that binds a row to the session/agent that wrote it, unforgeable
without a secret the writer's role cannot read. The second, once dispatch minting exists
(§3), is the minted-principal stamp. Header names, exact values, and size bounds are
the build's to fix in the spec's spirit; the bounds are LOAD-BEARING (the lesson of
kernel lineage delta [`s65`](FABLE-S65-REFUSAL-ATTEMPTED-KIND-SPEC.md) — the refusal
journal was made to record the attempted act kind because an unrecorded kind cost a
three-agent investigation to diagnose — applies here too: the identity path is exactly
where hostile input arrives — an oversized or malformed identity header draws a typed,
teaching refusal BEFORE any kernel call, never truncation, never pass-through).

**Service-side:** the identity headers are parsed into the L1 request context, then
threaded into `_psql()`'s per-request subprocess environment as PGOPTIONS GUC settings —
the SAME GUCs the kernel's s17/s21 substrate already reads and verifies. Per-request
subprocess env, never the server's own env (the exact confusion row 1467 witnessed).

**The trust property, stated once and enforced by construction:** the service is a
CONDUIT, not an authority. It never holds key material, never computes or verifies an
HMAC, never rewrites identity values — verification remains kernel-side (s17), exactly
as for a direct psql caller. A service compromise can therefore drop or garble identity
(fail-safe: unstamped rows, s21 NULL-never-distinct, claims refuse) but cannot MINT
verified identity. The build states this as an invariant and witnesses the negative
(a service-side forged/garbled stamp yields `stamp_verified=false`, never true).

## 2. Identity resolution order (declared, never silent)

Per request, the service resolves and records in the L1 context exactly one of:

1. **Minted-principal stamp present** — the dispatched-agent case (§3).
2. **Vendor stamp present, no minted principal** — the operator's own interactive
   session; restores the stamp-distinctness capability the
   [CLI rebase](FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md) (the migration of the
   operator verbs' write path off direct `psql` calls onto the HTTP boundary service)
   silently lost.
3. **Anonymous** — no identity headers.

Resolution is recorded (the diagnostic log's L1 context carries which case fired), and
the vocabulary is closed: a request carrying BOTH minted and vendor material is not a
fourth case — the minted stamp governs and the vendor stamp rides along to its own GUCs
(they occupy disjoint columns kernel-side; nothing merges).

## 3. Dispatch minting and the 4c defaults (ratified row 1471, binding here)

A scripted dispatch verb (`./autoharn` surface, self-application rule — no prose-steps
procedure) that the orchestrator runs at commission time: mints the delegate principal
(the [`s40`](../kernel/lineage/s40-principal-identity-events.sql) registration
machinery — the kernel lineage delta that made principal identity a typed, append-only
ledger fact — via the existing led verbs), writes the `dispatched-by` edge carrying
commission row ids and caveats (the delegation-condition vocabulary of kernel lineage
deltas [`s41`](../kernel/lineage/s41-principal-bindings-and-relations.sql) and
[`s64`](../kernel/lineage/s64-principal-stamps-delegation-conditions.sql)), and emits the
stamp material the child session's environment carries. Defaults, per sub-item 4c of
ledger row 1471 (the ratified defaults cited above):

- **no-redelegate ALWAYS** on leaf briefs; the independent-verification carve-out is by
  act TYPE; depth-N is explicit opt-in at the verb's surface.
- **Anonymous sessions keep NO write surface beyond journaled refusals.** Enforcement
  lands in two rungs: (a) THIS build — the service refuses anonymous authority-bearing
  writes with a typed, teaching disposition (the boundary already refuses plenty; this
  is one more typed refusal), with a config-declared grace posture the maintainer sets
  at rollout so the operator surface is never broken mid-migration (the CLI forwarding
  of §1 must demonstrably work for the operator FIRST — witnessed, then the refusal
  turns on); (b) NEXT WORLD — a fail-safe-additive kernel delta making the same refusal
  kernel-resident (adds a refusal only, which places it in the class-ratified
  fail-safe-delta family — the maintainer's standing 2026-07-09 ruling, stated in
  [CLAUDE.md](../CLAUDE.md) under "Class-ratified fail-safe deltas": a kernel delta that
  only ADDS refusals, witnessed on scratch on both polarities, enters the birth chain
  without a per-delta maintainer question; doubt about class membership routes to the
  maintainer — it is NOT part of this build).
- **Minted principals retire at session end.** The scripted close verb retires the
  principal (standing loss, s40 vocabulary). The eventual automatic trigger is a
  SessionEnd hook — hooks/ is frozen during live sessions, so the hook INSTALLATION is
  parked for the standing session-gap item (row 1448's gap) and this spec only defines
  it; until then the orchestrator's close verb is the mechanism, and an unclosed session
  leaves a principal whose standing the NEXT dispatch verb run sweeps (stated in the
  verb's own output, so the residue is loud, not silent).

## 4. What this spec does NOT do

This build makes none of the following changes: no kernel delta (the enforcement delta
above is explicitly deferred to its own authoring); no hooks/ edits (parked per the
live-session rule — both the spawn-gate hook, parent spec §3 item 2, and the SessionEnd
retirement hook); no change to direct psql callers (the interception convention is
untouched); no key management (none exists service-side, by design); no closing of the
specimen-class enumeration, which the parent spec's §1 deliberately declares OPEN (the
list of dispatch-failure classes — stale-copy coherence, ungated re-delegation, witness
identity — is expected to grow as operation surfaces new ones; this build closes none of
that growth off).

## 5. Witness plan (scratch, both polarities, red first)

RED: oversized identity header → typed teaching refusal, nothing reaches `_psql`;
malformed stamp → same; forged HMAC via the conduit → row lands `stamp_verified=false`
and the distinctness claim on it REFUSES (the s21 leg re-witnessed through HTTP);
anonymous authority-bearing write refused once the rung-(a) posture is on (and accepted
under the grace posture, with the resolution case logged — both postures witnessed).
GREEN: operator-shaped vendor stamp end-to-end — CLI env → headers → per-request GUCs →
stamped row with `stamp_verified=true` and `led stamp-distinctness` returning its FIRST
real pair on a served world (the capability row 1467 proved has never fired — that
observable flipping is THE acceptance criterion); minted-principal dispatch → edge
written, delegate's authority-bearing write attributed, retirement at close witnessed;
byte-identity of an accepted anonymous write pre/post under the grace posture.
DEPTH WITNESS (parent spec §5, executed here): on the installed harness, whether
PreToolUse fires inside depth-2/depth-3 child sessions and whether a dispatch-injected
env stamp survives into a grandchild — both polarities, degradation mode documented
honestly if the hook does not fire deep (kernel refusals hold regardless; the env-var
depth cap becomes the mandatory leaf-brief backstop, per §4.1). Read-only with respect
to hooks/ — it observes the seventeen installed hooks, edits nothing.

## 6. Closure statement

Quantification universe, per
[ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) Rule 2(a): the served identity paths are exactly
the requests reaching `_psql()` (single chokepoint, row 1467's own finding), and the
identity cases are the closed three of §2. Covered: both stamp families over that
chokepoint, the anonymous refusal at the service rung, dispatch minting/retirement via
the scripted verbs. Not covered, stated honestly: direct psql callers (already served by
the interception convention, untouched); kernel-resident anonymous refusal (next world's
delta); hooks-side spawn gating and automatic retirement (parked for the session gap);
out-of-band channels (workspace isolation's territory, per the parent spec).

## License

Public Domain (The Unlicense).
