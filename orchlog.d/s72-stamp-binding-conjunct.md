subject: a218a1b4
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

The AC batch's final delta: `kernel/lineage/s72-stamp-binding-conjunct.sql` — RBAC's
authenticated input (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §5 item 5).
Same runs-are-linear caveat as s70/s71 (see those sibling notes): **not applied to autoharn3**,
rides the next `--new-world` scaffold's `LINEAGE_CHAIN`.

**What a restarting orchestrator needs to know:**

- Two new kinds, the TENTH and ELEVENTH authority-bearing tokens alongside s60's original
  eight: `principal_stamp_bound` (binds a registered principal to a `stamp_agent` identity
  string — s17's hook-injected invocation string, e.g. `main`) and
  `stamp_binding_class_configured` (nominates which act class this conjunct governs, s60's
  `entitlement_class_configured` shape one axis over).
- **Empty by default — zero behavior change until a world arms it.** No act class is
  nominated at birth; conjunct (c) is a total no-op for every class until a
  `stamp_binding_class_configured` row names one. A fresh world's ordinary writes are
  byte-identical to pre-s72.
- **Once armed** over an act class, every future write in that class must ALSO carry a
  VERIFIED interception stamp (`stamp_verified = true`, never a mere string match) whose
  `stamp_agent` resolves to an in-force `principal_stamp_bound` row naming the acting
  principal. The refusal you'd meet on an armed world, verbatim from the banked fixture
  (`seen-red/s72-stamp-binding-conjunct/red.txt`): *"Ledger policy: entitlement refused (s72,
  factored acceptance predicate conjunct c, `<class>`) — act class '`<class>`' is nominated
  for the stamp-binding conjunct ...; this write's own interception stamp (verified=`<t/f>`,
  agent=`<agent-or-NULL>`) does not resolve to an in-force `principal_stamp_bound` row naming
  actor `<id>` as bound to that agent string. Remedy: ... route the write through the
  intercepted path; a verified write from an agent this actor has not bound needs the actor's
  own genesis-chained delegator to bind it first: `./autoharn led ledger-write --kind
  principal_stamp_bound --principal-subject <id> --stamp-binding-agent <agent> --principal-
  binding-active true`."* An unstamped write, a verified-but-wrong-agent write, and a
  forged-HMAC write claiming `agent=main` are all refused (three distinct fixture legs); the
  correctly-bound `main`-stamped write is accepted.
- **The ephemeral-dispatched-agent fork — reported, not resolved (row 601's own STOP
  instruction, honored rather than picked silently).** A dispatched subagent's `stamp_agent`
  is a harness-minted, unknowable-in-advance ephemeral id, never `main` — it cannot be bound
  in advance. Nominating `milestone_closure` or `gate_edge_supersession` (routinely closed by
  a dispatched subagent, not the orchestrator's main thread) under this conjunct with only
  `main`-bound principals available would refuse every legitimate subagent close — a real,
  disclosed friction cost, not a defect. A dispatch-time/first-verified-use binding path
  (binding the moment a subagent's real ephemeral agent id first becomes observable) is named
  as the fix, explicitly for **trust-protocol-v2** — NOT built here. If you're deciding what
  to nominate on a future world: the four pre-existing orchestrator-only tokens
  (`principal_registered`, `principal_role_bound`, `standing_lifecycle`,
  `entitlement_class_configured`) plus this delta's own two self-protecting tokens are safe to
  arm with `main`-only binding; `milestone_closure`/`gate_edge_supersession` are not, until that
  follow-on lands.
- **Disclosed limits, stated plainly rather than oversold:** binding is on `stamp_agent`
  ALONE, never the `(stamp_session, stamp_agent)` pair s21 uses for cross-session
  distinctness — single-trust-domain semantics, every session's `main` thread admitted as one
  voice, by design. No ASP twin exists for this conjunct at all (`judge`'s entitlement
  differential does not cover stamp-binding facts — UNEXERCISED, not claimed AGREE for that
  family). The schema-owner/superuser bypass stands, narrowed by the S2b split to a
  birth-only act, never a standing runtime exposure once a world has split.

Fixture evidence cited from the banked transcript (`seen-red/s72-stamp-binding-conjunct/
red.txt`, landed at merge `a218a1b4`) — ALL GREEN, including `verify-chain` intact through
every refusal and `judge` AGREE on the work-item layer — not re-run for this note.
