# ORCH-RCA-ATTRIBUTION-CLASS-2026-07-18 — banked verbatim RCA record
<!-- doc-attest-exempt: point-in-time investigation record, banked verbatim per ADR-0018 practice -->

What this is: the complete, unedited output of an out-of-frame, fresh-context Fable
root-cause analysis of the LED_ACTOR silent-misattribution class, commissioned by the
maintainer 2026-07-18 (commission quoted verbatim inside; ADR-0018 brief: witnessed
problem, evidence, LAW — no orchestrator diagnoses curated in; the orchestrating
session is itself a subject of this RCA and did not author it). Banked verbatim;
nothing below the rule is edited. Its remediation direction awaits maintainer
ratification; nothing in it is implemented by virtue of being banked.

---

# RCA + Class-Remediation Direction: silent misattribution of ledger writes (the LED_ACTOR class)

Fresh-context Fable investigation, 2026-07-17. Everything below is verified against artifacts read this session, cited by path/commit/row; nothing is repeated from the commission's prose on trust. Per the commission this is analysis and direction only — no implementation is written here.

---

## 1. The RCA

### 1.1 What the class is, mechanically

The kernel's write boundary (`kernel/lineage/s15-schema.sql:136-145`, same idiom in s13) is:

```sql
IF NEW.actor IS NULL THEN
  SELECT principal_id INTO NEW.actor FROM kernel.principal_role WHERE db_role = current_user;
END IF;
```

A NULL actor is silently filled from the connection role. On the CLI side (`bootstrap/templates/led.tmpl`), operator intent travels as an env var, `LED_ACTOR`, which each write path must *individually opt in* to reading (`resolve_actor()` + a `NULLIF(:'actor_name','')` bind in that path's own INSERT). A path that does nothing — literally an INSERT whose column list omits `actor` — produces NULL, and the kernel default fires. So **the defect path is the zero-effort path**: every new write site is born misattributing, and only work makes it honest.

Worse, one value — NULL — was made to carry at least four distinct meanings: intent never set; intent set to empty; intent set but *dropped by the CLI* (unwired path); intent set to an *unregistered name* (the subquery matches no row and returns NULL — the second latent defect commit `05bc000` itself names: "silently attributed to author, indistinguishable from unset"). That is a category collapse of exactly ADR-0000 Specimen 2's kind — incommensurable quantities merged into one currency — and it is why every instance was *silent*: the kernel cannot refuse what it cannot distinguish.

### 1.2 Why the class arose (design/idiom, not blame)

Two individually defensible decisions composed into the hazard:

1. **Kernel side: a fail-safe-looking default that is actually fail-*quiet*.** Attributing an actor-less row to the connection role is genuinely right for a solo world (one principal, `author`, writes everything). But ADR-0002's hierarchy (as imported by ADR-0012 P5) permits silent fallback *only when genuinely right*, and it is genuinely right only when default == intent. The trigger has no way to know that, because the intent channel (LED_ACTOR) terminates in the CLI and never reaches the kernel except as a possibly-absent column value.
2. **CLI side: intent transported per-call-site instead of per-session.** `led.tmpl` issues each write through its own psql heredoc with its own hand-copied preamble — I count **35 `SET ROLE` preambles** and (per commit `9e33dc7`'s reviewed enumeration) 15 `INSERT INTO ledger` sites across 7 dispatch points. Session-scoped facts (role, search_path, and — had it been designed that way — actor intent) have 35 writers. That is ADR-0012 cancer B (SSOT dissolved; the same knowledge re-encoded in N places) at the transport layer, and it makes "a write path that ignores operator intent" not merely representable but the *default state of any new path*.

The tell that this is idiom, not accident: the **same file solved the same problem correctly for the sibling channel**. `--event-time` is supported only on the generic path, and every other verb *refuses it loudly* — "never a silent drop; see the coverage guard" (led.tmpl ~line 60-64, guard at ~line 600-626). The difference is structural: a *flag* must pass through the dispatch parser, so an unsupported flag forces a decision; an *env var* requires no parse, so an unhandled one is ignored by construction. LED_ACTOR was an intent channel with **no forced read** — a channel whose ignoring is invisible in every signature. That is P8's lying-signature disease at file scale: the tool's interface (env var honored) was a contract no mechanism obliged any path to honor.

### 1.3 Why it recurred after being fixed once (run-7/8)

Commit `05bc000` (2026-07-11) is a textbook specimen of ADR-0000's 2026-07-02 Rule 2(a) amendment — **the class named at exactly the scope of the fix already built**. Its message says "LED_ACTOR honored on **every write path** via ONE resolver … per ADR-0000 the fix **forecloses the class**." It wired three paths (review, work claim, generic). At that commit the file *already contained* `led work open/depends/close` (added in `a73638d`, which precedes it). The quantification universe was never enumerated — no per-INSERT census, no closure statement listing sibling surfaces — so "every" was an umbrella claim with no witness, exactly what CLAUDE.md's claims-carry-witnesses rule and ADR-0013's 2026-07-02 amendment (a completion claim has a required shape) forbid. The presumption Rule 2(a) inverts — *the class as first named is presumed too narrow* — was not applied.

Then the recurrence engine ran: new INSERT branches kept being added (s29/s38 close constructors, s30 depends branches, resolve-violation) with **no net** obliging a new `INSERT INTO ledger` to bind actor. Enumeration fails open at the next instance (ADR-0011 Rule 4) — and here the enumeration wasn't even written down. The coverage *comment* meanwhile hardened the overclaim: after `8c4bb3b` it read "for **EVERY** ledger-writing verb — … alike (ONE resolution point … shared by all **four**)" — self-contradictory on its face (EVERY, then an enumeration of four, in a file with seven), and it stood until a reviewer forced honesty in `6561e8a`. A comment claiming coverage it lacks is a describing record that actively *launders* the gap: every later reader (and every later fix) inherits "this is closed."

Note also the ADR-0011 2026-07-02 amendment ("at the life-critical bar, the mechanism ships WITH the first fix") was already law on 2026-07-11 and was not obeyed by `05bc000`: the fix shipped with a witness (three polarities on a probe world) but **no recurrence net** — no gate, no fixture, nothing that would go red when the eighth INSERT was authored without an actor bind. Per ADR-0000 Rule 2(b), that is structurally the executive's to own — a recurrence never mechanized is a guard not built, not an implementer who erred.

### 1.4 Why discovery was late, piecemeal, and dependent on someone happening to look

The class has the exact profile ADR-0011's Context names — **invisible-at-authoring, visible-only-in-aggregate** — plus one aggravation: it is invisible *even in aggregate* as long as default == intent. In a solo world where `author` writes everything, misattribution to `author` is indistinguishable from correct attribution. Detection requires an environment where the default is *wrong* — and the first such environment was the downstream panel deployment deliberately retiring `author` from signing. Verified live in their ledger (read-only, DSN from `experience/autoharn-panel/deployment.json`): rows 1502/1599/1710/1716/1719/1732/1746 all `work_closed`, all `actor=1` (`author`), while `item-countersign` is principal 21; their `AUTOHARN_BACKFLOW.md` Finding 1 + addendum states it in their own words ("not caller error, a CLI gap … the one write every item's completion requires").

Now the purpose-built detection surfaces, honestly, one at a time:

- **seen-red fixture suites** (90+ corpora under `seen-red/`): they bank red evidence *for guards that exist*. A guard that was never wired has no fixture; `gates/fixture_census.py` checks every gate has a fixture, not that every *promise* has a gate. The class was an **absence**, and the seen-red discipline quantifies over presences. Additionally, every witness taken (including `05bc000`'s own three-polarity probe) exercised only the paths the fix touched — the witness universe was scope-of-fix, not class. This is CB-33's shipped-binding lesson (ADR-0011, 2026-07-02): green on the surfaces exercised, unverified on the surface actually serving the panel's closes.
- **Pre-commit gates** (`gates/`): every one is doc-, structure-, or kernel-shape-facing. None reads led.tmpl's INSERT sites for column coverage. There was no gate whose universe contained "does this write path honor the intent channel" — a gate cannot miss what is outside its declared universe, and no gate declared this universe.
- **kind_shape_manifest / allowlist gates**: `kind_shape_manifest_gate.py`'s own header scopes it to *kind-scoped* columns; `actor` is a CORE column, legal on every kind, trigger-filled, therefore definitionally outside the manifest. Correct behavior of a correctly-scoped gate — the miss is that no *sibling* manifest existed for intent-channel coverage.
- **The SQL/ASP differential (`./judge`)**: verifies that two independent encodings of the *rules* agree on the *rows*. Misattributed rows are well-formed rows; both encodings agree on garbage input. Attribution correctness is upstream of the differential's premise.
- **What DID catch instances 2–4, and why it worked**: the ADR-0017 doc B-pass caught `work open` (commit `e506806`: "Caught by a doc B-pass that traced the actual INSERT branches **after a spy's no-gotcha verdict**") because a documentation promise — "set LED_ACTOR for a dedicated-principal opener" (design/USER-RECIPES-FAQ.md ~line 308) — is a *falsifiable behavioral claim*, and the zero-context reviewer traced it to the mechanism. The unanchored code reviewer of that fix then caught instance 3 by refusing the comment's "EVERY" and enumerating (`6561e8a`). The panel's no-author policy caught instance 4 by changing the *oracle* — making the default a violation. The pattern across all three: **the only surfaces that caught the class were the ones that compared intent against mechanism.** Every code-facing surface verified the mechanism against itself (fixtures against shipped guards, gates against declared shapes, the differential against its twin encoding) — self-referential verification, which a coherent absence passes forever. ADR-0017's fresh-context probe is, structurally, the one instrument in the system built to test a *promise* rather than an implementation, and it is the one that fired. That is not luck to be celebrated; it is a finding: the system's intent-vs-mechanism comparison existed only in the documentation pipeline.

### 1.5 The tooling's mode of failure, as first-class subject

The maintainer called the surfacing "tacky," and the record supports a sharper word: the tooling **asserted coverage it did not have, twice, in its own self-description** — `05bc000`'s "every write path" (3 of ≥6 wired) and the post-`8c4bb3b` "EVERY … all four" comment (4 of 7). The tool's interface documentation was a lying signature; the discovery mode was therefore necessarily archaeological — someone reading prose against source. A CLI whose unwired paths had *refused* LED_ACTOR (the `--event-time` idiom already in the same file) would have surfaced instance 1 at the first attempted use, as a teach-text refusal, in seconds. The never-again designation is earned not by the misattribution alone but by the **silent no-op of an explicit operator instruction**: the operator said "sign as X," the tool said nothing, and did otherwise. In a system whose entire kernel design (stamps, countersigns, review_gap, segregation of duties) exists to make "who signed this" load-bearing, an attribution channel that fails silent is a hazard under CLAUDE.md's plank-with-a-nail standard — and it stood in reach of at least two shipped fixes that stepped past it.

---

## 2. The class-remediation direction (ADR-0000-grade)

The two questions, asked in order.

**(a) What type/shape makes the class unrepresentable?** The class is "a ledger-writing site that can ignore operator attribution intent." It exists because intent is transported per-call-site over a silently-defaulting substrate. The foreclosing shape moves intent **out of the call sites entirely**:

- **CLI layer — one session-boundary owner (ADR-0012 P1/P2).** Attribution intent becomes a fact of the *database session*, not of each INSERT's column list: one shared preamble (the single home the 35 hand-copied `SET ROLE` blocks should already be) sets a session variable (e.g. `SET app.led_actor = ...`) once, after `resolve_actor()`'s existence check. A write path then *cannot* ignore LED_ACTOR, because honoring it requires no per-site code — the zero-effort path becomes the honest path. This inverts the current defect polarity: today correctness is opt-in per site; under the session transport, only deliberate code could misattribute. (The 35-preamble duplication is itself the enabling P1 violation and should collapse to one owner in the same move — a corrective diff is new structure, ADR-0012's 2026-07-02 amendment.)
- **Kernel layer — split the NULL, and offer a strict posture.** `set_actor` gains the ability to distinguish the collapsed meanings: read the session intent variable first (intent explicitly carried); fall back to connection role only when no intent was declared. Then an **opt-in strict mode** per deployment (a kernel-table flag or the panel's proposed `principal.revoked` — their Finding 1, ask #1) turns "this principal may no longer sign" from verbal policy into a BEFORE-INSERT refusal. Under the panel's scenario, the first misattributed close would have been a loud kernel refusal instead of five silent wrong rows. Strict-off remains the solo-world default — the default-fill is genuinely right there, and ADR-0002 licenses it *only* there. Both kernel deltas are additive refusals/vocabulary — squarely inside CLAUDE.md's class-ratified fail-safe tier (witnessed both-polarity on scratch, judge AGREE), though the maintainer routes doubt as always.

**(b) What mechanism catches recurrence loudly (the net, ADR-0011 Rules 2/4, mechanism-ships-with-the-fix)?**

- **Gate/CI layer — an intent-channel coverage gate.** Mechanize `9e33dc7`'s hand-run 15-site enumeration: a gate that enumerates every `INSERT INTO <ledger>` in led.tmpl (structural predicate, not a pinned list — the s29/s30 detect-drift lesson in the git log applies verbatim) and asserts each either rides the session-intent preamble (or binds actor) or sits on a *named, reasoned* allowlist. Per the ADR-0011 2026-07-02 amendment, it ships with a **negative control** (red on the pre-`5ad05cf` tree shape or a synthetic unwired INSERT) and a fixture-census registration.
- **Generalize the channel, not the instance:** an **operator-intent-channel manifest** — the closed set of channels by which an operator's intent reaches a write (`LED_ACTOR`, `--event-time`, `--refs`, `--grade`, `--supersedes`, `--witness`, any future `LED_SERIES`) — each declaring its coverage set, with the gate asserting every dispatch path either *honors or loudly refuses* each channel. This is the `--event-time` coverage-guard idiom promoted from one flag's hand-built guard to a net over the class, and it is the same registry move ADR-0000 Revisit #4 Clause 2 minted for standards: the set of channels must not be corpus-discoverable-only, because the unregistered channel is exactly the one every audit misses.
- **Standing both-polarity fixtures:** a seen-red suite that runs every write verb under (i) unset, (ii) registered-non-default, (iii) unregistered LED_ACTOR — the panel's oracle (default ≠ intent) made permanent instead of accidental. `9e33dc7` witnessed this once on probe worlds; without a standing suite it is the describing record ADR-0011 says decays.

**Closure-statement candidate (ADR-0000 Rule 2(a), three parts):**

1. **Invariant:** an operator-declared attribution intent accompanying a ledger write either takes effect on that write or the write is refused with teach-text; a silent no-op of a declared intent is unrepresentable at the CLI transport and refusable at the kernel boundary.
2. **Quantification universe, enumerated:** *Write surfaces:* the 7 dispatch points / 15 INSERT sites in `bootstrap/templates/led.tmpl` (and structurally, any future `INSERT INTO ledger` there — the gate keys on the class, not the count); `bootstrap/new-project.sh`'s birth-chain seeding writes; any hook or engine path that writes ledger rows (I did not audit these — they enter the universe by the gate's structural predicate or are named as excluded, not silently omitted). *Layers that can silently default:* CLI env resolution (unset vs empty vs unregistered), CLI flag parsing (the swallowed-flag sibling class, `led-refs-flag-order-parser-bug`), SQL NULL fall-through (`NULLIF`, no-match subquery), the kernel `set_actor` default, and the read layer (views displaying misattributed rows as intended). *Detection surfaces obliged to catch recurrence:* the coverage gate, the both-polarity suite, the doc B-pass (a doc promise is a falsifiable claim), `./audit`. *Named as NOT covered:* a direct-psql writer supplying a wrong actor *explicitly* (writer-honesty trust bound, same as `event_declared_ts`'s stated bound); historical rows (below).
3. **Denomination check:** the bound is denominated in the detonating resource — *attribution rows*, checked per-INSERT-site and per-channel, never in a proxy ("the resolver exists," "the comment says every") — the exact proxy currencies the two overclaims were paid in.

**What deliberately NOT to build:**

- **Strict-by-default at the kernel.** It breaks the legitimate solo-world case and would be exactly the over-typing weaponization ADR-0000 Revisit #2 warns of. Strict is opt-in per deployment.
- **No backfill/correction of historical rows.** Runs are linear; the panel's misattributed rows are settled evidence, corrected (if at all) by superseding rows in their own ledger, never rewritten. Frozen worlds' `led` copies stay as-is (the `05bc000` precedent already ruled this).
- **No second attribution channel** (e.g. a per-verb `--actor` flag beside LED_ACTOR): two channels for one fact is cancer B at the interface.
- **No LLM-judged detection** for this class; every needed surface is deterministic.
- **No certification-bureaucracy apparatus** around it (the condemned-refgraph lesson): one gate, one fixture suite, one manifest — mechanisms, not paperwork.

---

## 3. Generalization, honestly bounded

**Is silent-wrong-by-default a recurring shape here? Yes — evidence actually found, cited:**

- `seen-red/pickup-connection-failure-silent-empty/` — the hydration verb returning silently empty on connection failure (the name is the finding).
- led.tmpl's run-11 `led show` note: an un-dispatched `show` silently accepted as `kind="show"`, burning a sequence id.
- `led-refs-flag-order-parser-bug`: flags silently swallowed into statement prose; its escalation note records that a WARN-only tripwire *re-bit twice in one day* before becoming a refusal — the same lesson (quiet signal ≠ net) one notch up.
- The provenance stamper corrupting files and **mis-attributing runs**, fixed three times (ADR-0011's 2026-07-02 amendment, commits `e787ccb`/`9902c18`/`5d2ef21`) — enforcement machinery itself silent-wrong.
- CB-33 (same amendment): load-bearing gates green while measuring a non-shipped backend.
- The what-did-we-miss RCA (ADR-0000 Revisit #4): five independent layers inheriting one silent omission, zero flags.
- The acronym gate (ADR-0017 Context): a detection surface wired into nothing — silently not enforcing.

The shape generalizes as: **a default or fallback whose correctness is conditional, running on surfaces where nobody has manufactured the condition's failure.** The single discipline most likely to catch the *next* instance in an unnamed subsystem is a **default-adversarial witness rule**, as a dated amendment to ADR-0011 Rule 3's probe-verify: *any behavior with a fallback/default carries, in its witness set, at least one surface where the default is the wrong answer* — the panel's no-author policy made deliberate and standing. Silent-wrong-by-default is exactly the defect that is green under every test whose environment agrees with the default; the discipline is to keep one environment that never does. **Marked as speculation:** whether that rule, or the intent-channel registry, catches a channel *nobody registers* — a registry cannot. The residual net for the truly unnamed is the one that fired here: the ADR-0017 B-pass treating every documentation promise as a falsifiable claim to trace to its mechanism. That is judgment-transported detection, honestly review-grade, and saying so is the ADR-0011 Rule 1 obligation.

---

## 4. Not covered, and confidence

**Deliberately not covered:** implementation of any of the above (out of mandate); an audit of non-led.tmpl ledger writers (hooks, engine, new-project.sh seeding) — the seven-path/15-INSERT claim rests on `9e33dc7`'s independently-reviewed enumeration, not my own re-count; the upstream autoharn ledger's own row 63 (I verified the panel DB live, not the upstream DB); ADR-0002 read in full (its hierarchy reached me via its verbatim imports in 0011/0012/0013 — the required-reading list did not include it, but my uses of it lean on quoted rules only); the s13-vs-s15 set_actor lineage differences beyond confirming the idiom is identical; and the maintainer's out-of-frame "principal design consult," which the commission says runs beside this and which I have not seen — deliberately.

**Confidence:** §1 (RCA) — high; every load-bearing claim is anchored to a commit, file line, or live DB row read this session. §2 (direction) — high on the diagnosis-to-shape mapping and the gate design; medium on the session-GUC transport's mechanical fit (the multi-invocation psql structure supports it since resolver and write are separate sessions today, so the SET must live in the write's own preamble — verified feasible, not prototyped). §3 — high on the cited instances; the proposed single discipline is a design judgment, and its stated limit is real. §4 — complete to my knowledge.
