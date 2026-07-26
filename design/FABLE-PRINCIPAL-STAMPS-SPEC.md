# FABLE-PRINCIPAL-STAMPS-SPEC — minted identity, recorded dispatch, monotone delegation

<!-- doc-attest-exempt: Fable-authored spec 2026-07-26, awaiting maintainer ratification;
the A:B:C loop runs when this spec is ratified and its build begins, not on the proposal
text. Removal condition: superseded by the build's completion record. -->

- **Status:** RATIFIED by the maintainer 2026-07-26, over the amended text including
  §4.1 (harness facts, Claude Code 2.1.220) and the §5 depth witness; ratification
  stated contingent on the nested-agent forward-compatibility check, which passed
  (ledger row 1441) before the word was given. Nothing is built yet; §7's choices remain
  open at the maintainer's leisure, and the agent-definition surface map (ledger row
  1443) may refine §3 item 3's carrier before the build spec is cut.
- **Basis (ledger rows, read together):** 1386/1387 (the maintainer's monotone sub-agent
  authority requirement and the harness tag-propagation assumption it rests on); 1414/1415
  (the wholesale-delegation specimen and its three defect classes, enumeration OPEN);
  1416 (the maintainer's delegation shapes: non-approval and conditional/countersigned
  delegation, count/history only as derivable caveats); 1420 (the witnessed no-redelegate
  vs mandated-independence deadlock and its carve-out); 1417 (the class-1 guard witnessed
  working in the field); 1411/1412 (v2 gates on MECHANICAL enforcement built from GENERIC
  primitives an end user can wield — nothing here may be a pattern-specific feature).
- **Relation to the entitlement frame:** this spec extends
  [FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md](FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md) — the
  s60/s62 acceptance predicate and chain walk are the substrate; every mechanism below
  enters as more of that substrate, never a parallel path.

## 1. The three specimen classes this spec answers (row 1415; enumeration declared OPEN)

1. **Stale-copy coherence** — a dispatched brief is a cached snapshot; amendments strand
   at intermediaries. (Witnessed: the row-1414 faceplant; the guard witnessed working
   unprompted at row 1417.)
2. **Ungated re-delegation** — at the harness level, dispatch is an ungated
   authority-bearing act with total inheritance by default; executor vs orchestrator
   existed only as prose.
3. **Accountability laundering** — an intermediary delivers a leaf's work as its own
   WITNESSED claims (witnessed: the same arc's confessed fabricated relay).

## 2. Design

### 2.1 Minted identity, recorded dispatch
Every dispatched agent session operates as its OWN registered principal — identity is
MINTED at dispatch, never inherited or carried. The dispatch act itself is a recorded
delegation: a `dispatched-by` relation row (the s41 vocabulary already carries the
relation; no new kind) written by the DISPATCHER (the s62 remedy: the delegator authors
the edge, never the delegate), classified `delegation_lifecycle` and therefore gated by
the dispatcher's own chain-to-genesis. A session with no minted principal and no recorded
dispatch edge is an ANONYMOUS session: it can read what its connection role permits and
nothing more; authority-bearing writes refuse.

### 2.2 Grant-subset monotonicity
A dispatch edge carries the delegate's effective grant, and that grant is a SUBSET of the
dispatcher's own effective grant at dispatch time, enforced at the write boundary: the
acceptance predicate walks the chain (as s60/s62 already do) and refuses any act outside
the intersection of every edge's grant along the path. Monotone non-increase is therefore
by construction — conjunction along the chain can only narrow — not by audit.

### 2.3 Caveats — the generic condition vocabulary (row 1416)
A delegation edge (acts-for or dispatched-by) may carry CONDITIONS, generic and closed
over conjunction; every hop's conditions apply to the whole suffix of the chain:
- **no-redelegate / depth-N** — the delegate may not write further dispatch edges (or may
  to depth N). Non-approval of delegation is the degenerate case: no dispatch entitlement
  granted at all.
- **must-countersign** — an act under this edge binds only when an s61
  signature-verified row by the named countersigner exists for it.
- **expiry / scope** — validity window; restriction to named act classes or worlds.
Count/history-shaped conditions (the maintainer's row-1416 note) are DERIVED caveats over
the chain walk the kernel already computes fresh at act time — never a served counter.
**Carve-out (row 1420, witnessed deadlock):** mandated independent-verification acts
(attestation B rounds, fresh-context reviews, countersigning itself) are their own act
class and are EXEMPT from no-redelegate BY TYPE — their value requires a distinct
principal; treating them as re-delegation deadlocks every strict leaf brief against every
independence requirement.

### 2.4 Commission re-hydration (class 1)
A commission is identified by its ledger row ids, carried on the dispatch edge. The
leaf's obligation is ONE generic act: before acting on the commission (and again before
finalizing), re-read those rows and anything superseding them via the read-only ledger
surface. Amendments become pull, not push: no intermediary can garble what the leaf reads
from the source. This is the guard row 1417 witnessed an uninstructed agent perform; this
spec makes it the stated contract of carrying a commission.

### 2.5 Witness identity (class 3)
A report's claims carry the minted identity of the principal that actually observed the
evidence. A relayed claim is marked relayed, never restated as first-person witness. The
enforceable half is ledger-side: rows written under a minted identity are attributed by
connection (s43 `set_actor`, never a name you type), so a laundered claim is a claim with
NO corresponding row by the claimed witness — checkable by review, refusable where the
report itself is a ledger write.

## 3. Enforcement surfaces (each generic; nothing pattern-specific)

1. **Kernel (one fail-safe-additive delta):** the conditions attribute on delegation
   edges + conjunction in the existing chain walk; the grant-subset check; the
   independent-verification act class. Only ADDS refusals — class-ratified family,
   scratch-witnessed both polarities, SQL/ASP AGREE (the ASP twin gains the same
   conjunction in its stratified closure, beside `in_force/1`, never into it).
2. **Hooks (the action-stream basis):** the hooks layer sees the Agent tool like any
   other tool call; a PreToolUse hook refuses spawn when the session's stamp says leaf
   (or depth exhausted) and refuses briefs that omit commission row ids. This is where
   class 2 becomes mechanical TODAY, from generic parts.
3. **Dispatch mechanics (verbs/briefs):** the dispatching orchestrator mints the
   principal, writes the edge, and injects the stamp (principal id + commission row ids +
   caveats) into the child session's environment.

## 4. Honest limits

- **The harness-propagation assumption (rows 1386/1387) is load-bearing and must be
  verified before it is relied on:** hook-visible stamp propagation into child sessions
  is a Claude Code behavior, not something this project controls. The kernel-side
  refusals hold regardless (an unstamped session simply has no authority); what degrades
  without propagation is only the hooks-side spawn gating.

### 4.1 Harness facts as of Claude Code 2.1.220 (raw-changelog witnessed 2026-07-26; ledger row 1441)

Nested agent spawning is now harness-native, and the harness grew primitives this spec's
mechanisms can stand on. Verbatim-sourced from the changelog (raw fetch, not a rendered
summary), stated here because they change the rank of the assumption above:

- **Nesting is on by default at depth 3** (2.1.219: "Subagents can now spawn nested
  subagents up to depth 3 by default (was 1); set CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1
  to disable nesting"; 2.1.217 had briefly defaulted it off). Class 2 (ungated
  re-delegation) is therefore a first-class harness capability, not a one-hop accident:
  this spec's depth caveats are load-bearing from day one.
- **Depth is a tracked harness concept** (2.1.187: resumed subagents restore original
  spawn depth; forked subagents count toward the cap) — a depth-N caveat has a harness
  fact to check against, not just our own bookkeeping.
- **Spawn gating has harness-native hooks BESIDE PreToolUse:** permission rules can deny
  by agent type and by tool parameter (2.1.186: "Agent(type) deny rules ... enforced for
  named subagent spawns"; 2.1.178: "Tool(param:value) syntax ... e.g. Agent(model:opus)"),
  and the spawn-depth env var is a blunt per-session-tree depth-0/1 enforcement. §3
  item 2 remains the per-edge mechanism (caveats differ per dispatch); these are
  defense-in-depth beneath it.
- **Hook events carry agent identity** (2.1.69: `agent_id`/`agent_type` on hook events;
  2.1.139: `x-claude-code-agent-id`/`parent-agent-id` request headers; SubagentStart/
  SubagentStop events exist) — the stamp the §3 hook needs to key on has a documented
  carrier.
- **The harness itself now asserts the class-3 boundary** (2.1.198: "Subagents now treat
  messages from the agent that launched them as normal task direction; an agent's
  message is still never treated as the user's approval"; 2.1.166: relayed SendMessage
  carries no user authority) — convergent with, not a substitute for, §2.5's
  ledger-side witness identity.
- **What stays UNWITNESSED until §5 runs:** that PreToolUse fires inside nested child
  sessions at depth 2+, and that a dispatch-injected environment stamp survives into a
  grandchild. The changelog documents the carriers; documented is not witnessed
  (house rule), so the §5 plan now includes the depth witness explicitly.
- **Out-of-band channels** (filesystem, environment, scrollback) are outside every
  mechanism here — workspace isolation is the only answer there, and it is not this
  spec's surface.
- **The specimen-class enumeration is OPEN** (the lessons posture,
  [law/MEMO-LESSONS-LEARNED-POSTURE.md](../law/MEMO-LESSONS-LEARNED-POSTURE.md)):
  operation will surface classes this spec has not named; the intake is ledger rows at
  contact, classes named on recurrence.

## 5. Witness plan (scratch, both polarities, red first)

RED — an unstamped session's authority-bearing write refused; a leaf-stamped session's
Agent-tool spawn refused by the hook; a re-delegation past depth refused at the write
boundary; an act outside the granted subset refused though the dispatcher could perform
it; a countersign-caveated act refused without the s61 row and accepted with it; the
row-1414 faceplant replayed as a fixture (amendment written after dispatch → leaf that
skips re-hydration acts on the stale brief → the finalize-time re-read catches it).
GREEN — the ordinary solo world unchanged (zero-friction leg); a two-hop dispatch chain
performing granted acts end-to-end; an attestation B round proceeding under a
no-redelegate leaf stamp via the carve-out class. SQL/ASP differential AGREE throughout.
DEPTH WITNESS (added 2026-07-26, §4.1): on the installed harness, witness whether
PreToolUse fires inside a depth-2 and depth-3 child session and whether a
dispatch-injected environment stamp survives into a grandchild — both polarities: a
leaf-stamped depth-2 session's spawn attempt refused if the hook fires there, and the
observed degradation mode documented honestly if it does not (kernel refusals still
hold; the spawn gate then covers hop 1 only, and §4.1's env-var depth cap becomes the
mandatory backstop in every leaf brief).

## 6. Closure statement

Quantification universe, per ADR-0000 Rule 2(a): the mechanisms of §2 close classes 1-3
of §1 FOR LEDGER-MEDIATED ACTS by sessions carrying (or refusing for lack of) minted
stamps, under the §4 assumption for the hooks surface. The universe of specimen classes
is declared OPEN; the universe of enforcement is exactly the two boundaries named in §3
items 1-2 plus the dispatch mechanics of item 3. Nothing outside those boundaries is
claimed.

## 7. Attention points (maintainer's leisure; none blocks ratification review)

1. Default caveat set for leaf briefs: no-redelegate always, or depth-1 by default?
2. Whether anonymous sessions keep any write surface at all (current inclination: none
   beyond journaled refusals).
3. Whether the minted principal is retired (standing loss) automatically at session end
   or persists until superseded.

## License

Public Domain (The Unlicense).
