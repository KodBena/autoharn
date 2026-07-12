# S21 SPEC — session-aware stamp distinctness (+ s19 residue fold-in)

Audience: orchestrator

Status: DESIGN, Fable-authored (session be693afb, 2026-07-09), PENDING MAINTAINER RATIFICATION
(assent batch item 4). Sonnet authors the DDL from this spec in the s20 house style and
scratch-witnesses it; APPLYING to any deployment remains the maintainer's act.

## Defect 1 — distinctness is session-blind (falsely refuses honest cross-session review)

s17's `validate_independence` and the `review_stamp_distinctness` view decide "distinct
invocation" from `stamp_agent` ALONE. Every interactive session's main thread stamps
`agent='main'`, so two DIFFERENT sessions' main threads are indistinguishable: a genuinely
independent second-session review claiming `technical` is refused as same-invocation. Fails
safe (refuses an honest claim; never admits a false one) — witnessed consequence: e18's
second-session reviewers could pass only as subagents.

**Fix (the type answer):** an invocation's identity is the PAIR `(stamp_session, stamp_agent)`.
- `validate_independence`: a technical/managerial/financial claim is refused iff either row is
  unstamped/unverified, OR the pair on the review equals the pair on the regards-target.
  Distinct session with equal agent labels ('main','main') is DISTINCT. Same session with
  distinct agents (main vs subagent UUID) remains DISTINCT (preserves the witnessed e17 shape).
- `review_stamp_distinctness.same_invocation`: recomputed on the pair, same rule.

**Compatibility:** strictly more permissive than agent-only for cross-session (retires the
false refusal), identical for same-session. Insert-time trigger only — no retroactive effect;
e17/e18's passing rows (distinct agents, same or distinct sessions) pass under both rules.

**Closure statement.**
- Invariant: every consumer of invocation-distinctness derives it from the (session, agent)
  pair; no consumer reads stamp_agent alone as an identity.
- Universe: `validate_independence` (s17-independence), `review_stamp_distinctness` (s17-stamp)
  — and the DDL author greps the full lineage for any other reader of `stamp_agent`/
  `same_invocation` and either covers it or names it not-covered with the reason. Named as NOT
  covered: `stamp_valid()`/`set_stamp` (they verify HMAC integrity, not distinctness — correct
  as-is); the engine EDB (carries no stamp vocabulary, by design).
- Denomination: identity is the pair, not a proxy for it; NULL/'' session or agent on a
  verified-stamp row is unrepresentable upstream (set_stamp writes both or neither) but the
  trigger must still treat a NULL half as NOT distinct (fail-safe, never fail-open).

## Defect 2 (fold-in) — s19 residue: validate_* resolve via session search_path

BACKLOG's filed s19 residue (2026-07-09): `validate_enacts/review/amends/answers` were scoped
out of s19's closure on the premise "resolved by the role's login search_path", which SET ROLE
does not honor — masked today only by the documented explicit `SET search_path`. Fix exactly
as the filed entry proposes and as s19 itself did for set_actor/set_stamp: each of the four
functions gains per-function `SET search_path = :"schema", pg_temp`. Universe: the four named
functions; set_actor/set_stamp already carry it (s19); no other in-chain SECURITY-relevant
function lacks it (DDL author verifies by grep and states so).

## Witness protocol (Sonnet-executable)

Scratch schema pair in the toy db (s21probe/...), apply chain + s20 + s21, then witness:
(1) same-session distinct-agent technical review passes (e17 shape preserved);
(2) cross-session main-vs-main technical review passes (the retired false refusal — simulate
    two sessions by two distinct stamped invocations with agent='main', different session ids;
    stamps can be forged in the probe by computing the HMAC with the probe's own secret —
    that is legitimate in a probe, it owns its secret);
(3) same-pair technical claim refused (the SoD-of-invocations negative control);
(4) unverified-stamp technical claim still refused; NULL-half treated as not distinct;
(5) with only s20 (not s21): the linked-row inserts fail WITHOUT explicit SET search_path via
    SET ROLE (reproduce the residue), then with s21: they succeed with no session-level SET —
    the s19-residue witness, positive and negative.
