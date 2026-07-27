# FABLE-DISPATCH-MECHANICS-SPEC — one HTTP-borne identity plumbing for stamps and minted principals

<!-- doc-attest-exempt: Fable-authored spec awaiting maintainer ratification 2026-07-27;
the A:B:C loop runs on the build, not the proposal text. Removal condition: superseded by
the build's merge record, or rejection. -->

- **Status:** PROPOSED 2026-07-27. This is [FABLE-PRINCIPAL-STAMPS-SPEC.md](FABLE-PRINCIPAL-STAMPS-SPEC.md)
  §3 item 3 (dispatch mechanics) built out, per the maintainer's standing word on ledger
  row 1471: the confirmed stamp finding "enters the dispatch-mechanics build spec as a
  named requirement — one HTTP-borne identity plumbing serving both minted principals and
  vendor stamps."
- **Basis:** rows 1463/1467 (vendor stamps NEVER reach the served path — PGOPTIONS is a
  launch-time env var, `_psql()` copies the server's own environment; no stamped
  distinctness pair has EVER formed on the real deployment; fail-safe confirmed at
  s17/s21), 1468 (deliberately not patched narrowly — no second identity mechanism),
  1471 (the 4c ratified defaults, binding at THIS build), and the parent spec's §4.1
  harness facts and §5 depth witness.
- **Dependency:** the L1 per-request context middleware of
  [FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md](FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md)
  (RATIFIED, in build). Identity parses INTO that context object — it was defined once
  for both consumers by design. This build sequences strictly after that merge.

## 1. The one channel (replaces nothing; fills the witnessed void)

**Client-side:** the CLI (`led.tmpl` via `serving/boundary_cli_client.py`) reads the
identity material already present in its own process environment — the vendor stamp the
existing interception convention injects (`app.vendor_session`/`app.vendor_hmac`), and,
once dispatch minting exists (§3), the minted-principal stamp — and forwards it as
request headers on every boundary call. Header names, exact values, and size bounds are
the build's to fix in the spec's spirit; the bounds are LOAD-BEARING (the s65 lesson:
the identity path is exactly where hostile input arrives — an oversized or malformed
identity header draws a typed, teaching refusal BEFORE any kernel call, never truncation,
never pass-through).

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
   session; restores the stamp-distinctness capability the CLI rebase silently lost.
3. **Anonymous** — no identity headers.

Resolution is recorded (the diagnostic log's L1 context carries which case fired), and
the vocabulary is closed: a request carrying BOTH minted and vendor material is not a
fourth case — the minted stamp governs and the vendor stamp rides along to its own GUCs
(they occupy disjoint columns kernel-side; nothing merges).

## 3. Dispatch minting and the 4c defaults (ratified row 1471, binding here)

A scripted dispatch verb (`./autoharn` surface, self-application rule — no prose-steps
procedure) that the orchestrator runs at commission time: mints the delegate principal
(the s40 registration machinery via the existing led verbs), writes the `dispatched-by`
edge carrying commission row ids and caveats (s41/s64 vocabulary), and emits the stamp
material the child session's environment carries. Defaults, per 4c:

- **no-redelegate ALWAYS** on leaf briefs; the independent-verification carve-out is by
  act TYPE; depth-N is explicit opt-in at the verb's surface.
- **Anonymous sessions keep NO write surface beyond journaled refusals.** Enforcement
  lands in two rungs: (a) THIS build — the service refuses anonymous authority-bearing
  writes with a typed, teaching disposition (the boundary already refuses plenty; this
  is one more typed refusal), with a config-declared grace posture the maintainer sets
  at rollout so the operator surface is never broken mid-migration (the CLI forwarding
  of §1 must demonstrably work for the operator FIRST — witnessed, then the refusal
  turns on); (b) NEXT WORLD — a fail-safe-additive kernel delta making the same refusal
  kernel-resident (adds a refusal only; class-ratified family; routed per the standing
  class rules when authored — it is NOT part of this build).
- **Minted principals retire at session end.** The scripted close verb retires the
  principal (standing loss, s40 vocabulary). The eventual automatic trigger is a
  SessionEnd hook — hooks/ is frozen during live sessions, so the hook INSTALLATION is
  parked for the standing session-gap item (row 1448's gap) and this spec only defines
  it; until then the orchestrator's close verb is the mechanism, and an unclosed session
  leaves a principal whose standing the NEXT dispatch verb run sweeps (stated in the
  verb's own output, so the residue is loud, not silent).

## 4. What this spec does NOT do

No kernel delta (the enforcement delta above is explicitly deferred to its own
authoring); no hooks/ edits (parked per the live-session rule — both the spawn-gate
hook, parent spec §3 item 2, and the SessionEnd retirement hook); no change to direct
psql callers (the interception convention is untouched); no key management (none exists
service-side, by design); no closing of the OPEN specimen-class enumeration.

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

Quantification universe, per ADR-0000 Rule 2(a): the served identity paths are exactly
the requests reaching `_psql()` (single chokepoint, row 1467's own finding), and the
identity cases are the closed three of §2. Covered: both stamp families over that
chokepoint, the anonymous refusal at the service rung, dispatch minting/retirement via
the scripted verbs. Not covered, stated honestly: direct psql callers (already served by
the interception convention, untouched); kernel-resident anonymous refusal (next world's
delta); hooks-side spawn gating and automatic retirement (parked for the session gap);
out-of-band channels (workspace isolation's territory, per the parent spec).

## License

Public Domain (The Unlicense).
