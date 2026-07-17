# ORCH-METACONSULT-RCA-CLASS-WIDTH-2026-07-18 — banked verbatim consultation record
<!-- doc-attest-exempt: point-in-time consultation record, banked verbatim per ADR-0018 practice -->

What this is: the complete, unedited output of an out-of-frame, fresh-context Fable
consultation commissioned by the maintainer 2026-07-18 to apply ADR-0000's inverted
presumption ("the class as first named is presumed too narrow") to the banked
attribution-class RCA itself (design/ORCH-RCA-ATTRIBUTION-CLASS-2026-07-18.md). The
maintainer pre-declared an idempotent outcome as standing evidence on its own; the
outcome was NOT idempotent — see the findings. ADR-0018 brief: the dictum, the object,
the evidence, the LAW; no candidate wider classes front-loaded. Banked verbatim;
nothing below the rule is edited.

---

# Consultation: ADR-0000 Rule 2(a) dictum applied to ORCH-RCA-ATTRIBUTION-CLASS-2026-07-18

Method note: every claim below marked WITNESSED was verified this session against files, commits, or live read-only queries; nothing is repeated from the RCA's prose on trust. Conjecture is marked as such. Per the commission, HOLDS findings are stated with the same care as WIDER ones.

## 1. Axes on which the presumption was applied

1. **The class name** — "silent misattribution of ledger writes" / "a ledger-writing site that can ignore operator attribution intent."
2. **The quantification universe, write surfaces** — "7 dispatch points / 15 INSERT sites in `bootstrap/templates/led.tmpl`; new-project.sh seeding; any hook or engine path."
3. **The quantification universe, kernel surfaces** — "the kernel `set_actor` default (`s15-schema.sql:136-145`, same idiom in s13)."
4. **The detection-surface list** (§1.4 and closure part 2's "detection surfaces obliged").
5. **The named exclusions** — direct-psql writer honesty; historical rows; upstream row 63.
6. **The §3 generalization** — "silent-wrong-by-default," its instance list, and the default-adversarial witness rule.
7. **The closure-statement candidate itself** — whether its invariant's boundary coincides with the edge of the fix that motivated it (the exact tell Rule 2(a) names).

## 2. Per-axis findings

### Axis 1 — the class name: WIDER, and the sibling is live today, not future

The RCA generalizes to an "operator-intent-channel manifest" (§2b) and lists sibling channels (`--event-time`, `--refs`, ...) — so the *direction* already gestures outward. But the RCA presents those siblings as manifest work for the future, and its closure invariant (part 1) is attribution-only. The sibling class is live in the current, fully-fixed tree:

**WITNESSED:** `led.tmpl:457-472` — the shared top-of-file loop parses `-f -e --supersedes --amends --amends-scope --answers --refs --concern --evidence --confidence --event-time` *before* dispatch, for every verb. Only `--event-time` has a per-verb coverage guard (lines ~615-626). The `review` path's INSERT (line 1258) carries `(kind, statement, regards, actor)` — no refs, no supersedes, no evidence, no confidence; `work claim` (1554) carries `(kind, work_slug, statement, actor)`; `work close` (2043) carries none of the shared-loop channels. So `./led --refs row:12 review 42 attest technical "basis"` parses `--refs`, writes the row, and drops the value with no error — a silent no-op of an explicit operator instruction, mechanically identical to the LED_ACTOR class. The `refuse_flag_in_statement` guard (706-732) catches only flags placed *after* the statement; flags placed *before the verb* on a non-supporting verb are swallowed by construction. This is distinct from the `led-refs-flag-order-parser-bug` the RCA's universe names (that was the trailing-flag parse bug, since escalated to a refusal).

The class in its general form is therefore: **a per-call-site-transported operator-intent channel over a silently-lossy substrate** — LED_ACTOR was one instance; roughly 8 channels × 6 non-generic verbs are standing instances now. The RCA's own §1.2 analysis ("a channel with no forced read") already states this generality; its class *name* and closure *invariant* then narrow back to attribution.

### Axis 2 — write-surface universe: one WIDER (load-bearing), remainder HOLDS and partially discharged

**HOLDS / discharged:** I audited the surfaces the RCA left as "not audited, enter by predicate or are named excluded." WITNESSED by grep sweep: hooks/ contains no ledger INSERT (only teach-text mentions); engine/ writes only scratch and derived-join schemas (`*_scratch.py`, `acts_join.py` — copies, not the source ledger); `bootstrap/new-project.sh` and `track-work.sh` insert only `principal`/`stamp_secret`/`chain_genesis`, no ledger rows (the RCA's "birth-chain seeding writes" entry is slightly over-inclusive, harmlessly); the panel backend's sole write path shells out to the world's `./led` with LED_ACTOR set (`tools/autoharn-panel/backend/extensions/autoharn/cosign.py:1-52`). The RCA's led.tmpl census also checks out: exactly 15 `INSERT INTO ... ledger` sites, 35 `SET ROLE` preambles (both counted this session), and all 15 currently bind `actor`.

**WIDER — the serving-surface axis (this is the load-bearing finding).** The universe is denominated in "INSERT sites in `bootstrap/templates/led.tmpl`" — a file identity. The defect detonates on *deployed executions* of that file, and the deployment topology is not scaffolded copies but shims into a sibling checkout. WITNESSED, four legs:

- `/home/bork/w/vdc/1/experience/autoharn-panel/led` is a 3-line shim: `exec ... /home/bork/w/vdc/1/experience/autoharn/bootstrap/templates/led.tmpl`.
- That serving checkout sits at `fe70575`; it contains `e506806` (work-open fix) but `9e33dc7` and `5ad05cf` (depends/close/resolve-violation fix, merged 2026-07-17 in this repo) are **absent from its object store** (`git cat-file -t 9e33dc7` fails there). Its `work_closed` INSERTs (its led.tmpl lines 1882, 2018) carry no `actor` column at all.
- Live panel ledger (read-only, DSN from the panel deployment.json): rows **1765 and 1768**, both `work_closed`, both `actor=1` (`author`), both 2026-07-17 — *new instances beyond the RCA's cited set (1502...1746), written after the fix landed in this repo* — while the same day principal 21 (`item-countersign`) correctly signed 71 rows through the wired `review` path.
- No surface in the RCA's detection universe (the proposed gate, the fixtures, `./audit`) runs against a deployment's serving checkout; nothing obliges the shim's target to carry any minimum commit.

So the class the RCA declares "closed across every ledger-writing path" (led.tmpl's own current comment) remains **open and producing rows at the one deployment whose oracle can see it**. The RCA's §4 does not name deployment/serving freshness as covered or excluded — the exclusion is inherited from thinking in file identities, not argued. This is a superclass instance of the RCA's own CB-33 citation: green on the tree exercised, unverified on the surface actually serving the panel's closes — recommitted one level up, at checkout granularity.

### Axis 3 — kernel surfaces: WIDER on enumeration, minor; one sibling checked and discharged

**WIDER (minor):** the RCA cites the idiom at s15 "same idiom in s13." WITNESSED: the idiom also lives in `s14-schema.sql:188`, and `set_actor` is *re-declared* by `s19-trigger-search-path.sql:64` (the live function body in every s19+ world), with trigger-ordering dependencies noted in s17/s21/s26. The RCA's §4 names "s13-vs-s15 differences" as not covered but does not name s14 or the s19 re-declaration. For remediation this matters mechanically: the "split the NULL" delta must land against the lineage head's declaration, and the s29/s30 detect-drift lesson the RCA applies to its *gate* applies equally to `set_actor` itself (behavior-fingerprint, not pinned file).

**HOLDS (argued exclusion, checked and discharged):** `kernel/lineage/nla-schema.sql:72` carries the same silent default in column-DEFAULT form (`actor text NOT NULL DEFAULT current_user`). Its preamble argues single-writer isolation makes connection-identity attribution correct by construction (default == intent structurally, one principal). The presumption checked outward here and discharged: this is the solo-world case ADR-0002 genuinely licenses, argued in the artifact itself.

### Axis 4 — detection-surface list: HOLDS, with two nuances

WITNESSED: the gates/ directory contains no intent-channel or INSERT-column-coverage gate (`column_complete_gate.py` is view-vs-table shape, a different mechanism; `ledger_reader_allowlist` is read-side). The RCA's per-surface analysis of why each existing surface could not see the absence survives my re-walk. Two nuances, neither overturning it:

- The kernel's same-actor-review refusal was a pre-existing surface where the default *was* adversarial for one path (a misattributed review of one's own row refuses loudly — led.tmpl's own comment at ~1245 relies on it). §1.4 doesn't list it; it guards only reviews, so the analysis stands, but it is the one in-kernel instance of the RCA's proposed "keep one environment where the default is wrong," and worth naming as the existing seed of that discipline.
- The doc B-pass — the instrument §1.4 crowns — itself rides an attribution trust bound: `gates/doc_attestation_presence.py:62-64` states plainly that B-vs-A identity is not policed (an argued exclusion, ADR-0017's own identity-enumeration-fails-open reasoning, so this is *not* a silent gap — but the RCA's "only intent-vs-mechanism comparison surfaces fired" finding should carry the caveat that the firing surface's own who-did-this is honor-system).

### Axis 5 — named exclusions: HOLDS, one discharged

Direct-psql writer honesty: HOLDS — same trust bound the kernel states for `event_declared_ts`; no mechanism can close it without a different threat model. Historical rows: HOLDS — runs-are-linear governs, and the panel corrects by superseding rows in its own ledger. Upstream row 63: partially discharged this session — WITNESSED live: `autoharn1` ledger row 63 is `work_claimed`, `actor=1` (`author`), 2026-07-12, consistent with the commit-prose forensics (whether it is the exact row the run-7 note meant, or a run-world twin now dust, I cannot distinguish; the shape exists upstream either way).

### Axis 6 — the §3 generalization: HOLDS on its instances; one sibling dropped without argument

The cited instances all check out where I probed them. But the RCA harvested the panel's Finding 1 asks #1 (`principal.revoked`) and #3 (uniform `resolve_actor`) and silently dropped **ask #2**: `register-principal`'s `ON CONFLICT (name) DO NOTHING`. WITNESSED: `led.tmpl:880`, live in the current tree. This is the same shape the RCA's §1.5 says earns the never-again designation — an explicit operator instruction silently no-opped — inside the same attribution subsystem, in the RCA's own evidence source, and it is worse than benign: registering an existing name with a *different* `agent_class` silently leaves the old class standing, a divergence between declared and recorded identity with no signal. Neither §2 nor §3 names it, covered or excluded. Modest WIDER.

### Axis 7 — the closure-statement candidate: WIDER, and it is the dictum's own tell

Part 1's invariant quantifies over "operator-declared **attribution** intent"; part 2's gate bullet asserts each INSERT "rides the session-intent preamble (or binds actor)." Under that closure statement, the live `--refs`-on-review silent drop (Axis 1) passes green — the invariant's boundary coincides exactly with the edge of the fix already built (`5ad05cf`), which is the tell Rule 2(a) names verbatim. The manifest bullet in §2(b) *does* state the right wider invariant ("every dispatch path either honors or loudly refuses each channel"), so the RCA contains its own correction — but as remediation hardware, not as the closure statement the class would be certified against. A closure statement narrower than the remediation it accompanies is the overclaim mechanism of `05bc000` in a politer form.

## 3. What the WIDER findings change about the remediation direction (direction only)

1. **The universe must be denominated in serving executions, not file identities.** Before any of §2's machinery, the cheapest real remediation is operational: the serving checkout at `/home/bork/w/vdc/1/experience/autoharn` must carry `9e33dc7`/`5ad05cf`, or the panel keeps writing misattributed closes daily (rows 1765/1768 prove it is doing so now). Direction: the closure universe gains a third column — deployments and the checkouts their shims exec — and the recurrence net gains a deployment-freshness surface (a deployment's verbs asserting a minimum lineage/commit of the tree they exec, in the spirit of the existing verify-chain posture; the "worktree bases are stale" ruling is the same lesson already ratified for builders).
2. **The gate keys on the channel *set*, not the actor channel.** The shared parse loop (457-472) and `LED_FLAG_VOCAB` (706) are already the one-list SSOT of channels; the gate's predicate should be "every channel the shared loop parses is, per dispatch path, honored or loudly refused" — the `--event-time` guard generalized — otherwise the gate certifies closure over a class with eight live siblings standing.
3. **The kernel delta targets the lineage head's `set_actor`** (s19's re-declaration and later trigger-order constraints, not s15's frozen text), fingerprinted per the detect-drift lesson the RCA already cites for its gate.
4. **Carry the panel's ask #2** (duplicate-register refusal, or at minimum refuse on class mismatch) into the same additive-refusal delta family, or name it excluded with a reason.

## 4. Deliberately not examined

Implementation of anything above; any write anywhere (none were made — all DB access was SELECT-only under the deployments' own roles); executing the live `--refs`-drop witness (it would write a row — the finding rests on code reading of the parse loop and INSERT column lists, marked as such); the original run-7/run-8 world schemas (dust under runs-are-linear); hooks' non-ledger journals; the panel frontend; `tools/makespan-scheduler`; ADR-0002/0005/0008 in full (used via their quoted imports in 0011/0013/0017, same bound the RCA declared); the maintainer's out-of-frame principal-design consult (unseen, deliberately, same as the RCA); the stamp/session (s17/s21) attribution machinery beyond trigger-ordering references — a conjectural sibling ("session identity silently defaulted") I did not probe.

## Confidence

§2 Axis 1: high (code-witnessed, not executed). Axis 2: high — the serving-surface finding rests on four independent witnesses including live rows. Axis 3: high on the grep facts, the remediation implication is judgment. Axis 4: high on the gate census; the two nuances are observations, not defects. Axis 5: high. Axis 6: high on the witness, modest in weight. Axis 7: high that the closure text is actor-scoped; that this constitutes the Rule 2(a) tell is an interpretive claim I hold with medium-high confidence since the RCA's own manifest bullet shows the author saw the wider invariant.

**The bottom line, in the dictum's terms:** the RCA is a strong document whose *analysis* already reaches the general class; its *naming* — the closure invariant and the universe's denomination — contracts back to the attribution instance and to one file in one checkout. The presumption of too-narrow is not discharged: two siblings are live and witnessed (the non-actor channel drops in the fixed tree; the panel's still-misattributing closes through a stale serving checkout), one sibling was harvested-and-dropped without argument (register-principal's silent no-op), and the widest finding is that the class detonates per serving execution while every proposed net quantifies per repository file.
