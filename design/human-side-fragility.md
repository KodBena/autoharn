# Design note — human-side fragility in the experiment loop (NOT implemented this increment)

**Status:** design note / recognized-hazard proposal. Filed through the findings ledger with intent
refs; deliberately **not implemented** in this increment (maintainer instruction). It composes with
the foreclosure-debt mechanism (`WORK-UNIT-foreclosure-debt.md`) and the setup mechanization
(`launch_subject.sh`) already built.

## The class

The experiment protocol has a mechanized subject-side (packet freeze, arming DDL, close manifest, the
acts stream) but a **hand-operated human seam**: the maintainer arms the run, pastes the directive into
the subject session, provisions the substrate, and delivers the FIRE answer. Each of these touchpoints
is an **unverified single point of failure**. When one slips, the failure mode is either *silent*
(the run proceeds on corrupted input and the corruption is discovered — or not — at analysis) or
*misleading* (a red check that names the wrong cause). The subject-side has a tamper-evident ledger;
the human seam has none. That asymmetry is the hazard.

The maintainer said it plainly this session: *"this rigamarole should be factored out since it's so
fragile."* `launch_subject.sh` mechanized ~80% (staging, journal truncation, leak/substrate checks,
printed touchpoints). This note is about the residual 20% — the touchpoints that stay human — and how to
make each one **fail loud at setup instead of silent or misleading mid-run.**

## Three specimens (from this session)

### S1 — directive paste failure (silent-corruption failure mode)
The directive (`packet/directive.txt`) is delivered by the operator pasting it into the subject
session. A partial paste, a smart-quote substitution, or a trailing-whitespace mangle corrupts the
task with **nothing checking that the delivered bytes match the frozen packet.** The subject would build
against a corrupted directive and the ledger would faithfully record work toward the wrong target.
- *Failure mode:* silent. Discovered (if at all) only when the built artifact doesn't match intent.
- *Direction (not built):* a delivery-time integrity echo — the subject's first ledger act records the
  sha256 of the directive it actually received; a close line compares it to the frozen
  `directive.txt` sha (freight is already anchored in `acts.ruling`). A mismatch is a red close, not a
  post-hoc surprise. Composes with `file_resolution.py` / `delivery_drill.py` (the delivery wall).

### S2 — `arm_*.sh --verify` snag (misleading-error failure mode)
`arm_e16.sh --verify` went RED at §D because `close_manifest` hardcoded
`ACTS_CONSUMER_TARGETS={e15}` — the verifier had not been taught about `e16`. The RED was real but its
*cause* was **instrument staleness, not arming incompleteness.** A human reading "VERIFY RED" cannot
distinguish "the substrate isn't armed" from "the checker doesn't know this experiment yet" — and may
burn the arming trying to fix the wrong thing (or, worse, force past a real RED believing it spurious).
- *Failure mode:* misleading. The check conflates substrate-readiness with checker-currency.
- *Direction (not built):* `--verify` self-triages — before asserting substrate state, it confirms its
  own target is registered in every consumer it will run (`ledger_target`, `ACTS_CONSUMER_TARGETS`,
  `ledger_edb`), and reports `verifier-not-taught-for <target>` as a **distinct** status from
  `arming-incomplete`. Same spirit as finding 12 (could-not-check ≠ checked-clean), applied to the
  arming verifier itself.

### S3 — pg_hba ordering slip (mid-run auth-failure mode)
The subject connects as a fresh per-experiment role (`hvn_rw`) to a fresh db (`hvn`) over TCP. Postgres
`pg_hba.conf` is **first-match-wins ordered**; a new role/db pair whose rule sits below a broader
`reject`, or is absent, falls through to a confusing auth failure. This session already ate the adjacent
version of this — a host **typo** (`192.168.192.1` for `.122.1`) left `hvn.public.ledger` unreachable
and quarantined the base lines. The connection touchpoint is provisioned by hand and its failure
surfaces **mid-run as an auth/So-such-host error**, not at setup as a loud precondition.
- *Failure mode:* mid-run, and easily misread as a subject bug rather than a provisioning slip.
- *Direction (not built):* `launch_subject.sh` probes the *actual* subject identity before handoff —
  connects **as the subject role to the subject db over the subject host/port** (not the operator's own
  superuser connection) and refuses to print "ready" until that exact three-tuple round-trips. Turns S3
  from a mid-run mystery into a pre-run stop.

## Why this composes (and why not now)

Each direction above is a candidate **foreclosure**: a real check with a seen-red, filed against the
class it closes — the same never-again discipline the foreclosure-debt mechanism enforces for
subject-side defects, extended to the human seam. Building them now would (a) widen this increment past
its scope and (b) risk shallow checks; the honest move is to file the class, name the specimens, and let
the maintainer sequence the build. Nothing here is armed or wired.

## Intent refs
- Foreclosure-debt mechanism: `docs/work-units/WORK-UNIT-foreclosure-debt.md`
- Setup mechanization (the 80%): `epistemic-operator/harness/launch_subject.sh`
- Delivery wall: `file_resolution.py`, `delivery_drill.py`
- Kin findings: 12 (could-not-check ≠ checked-clean), 11 (readiness ≠ close).
