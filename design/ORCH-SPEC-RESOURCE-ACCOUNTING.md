# ORCH-SPEC-RESOURCE-ACCOUNTING — usage accounting and the deontic register

Audience: orchestrator (design spec; implementation stages are Sonnet-executable per §8).
Status: Fable-authored 2026-07-12, from the maintainer's same-morning asks (§1). This is a
COMPANION to [ORCH-SPEC-RESOURCE-REGISTRY.md](ORCH-SPEC-RESOURCE-REGISTRY.md) (the
capability-registry spec, attested 2026-07-12), not an amendment of it: that document's
attestation stands untouched, and under the zero-context-reader law's binds-on-touch rule
([law/adr/0017](../law/adr/0017-the-zero-context-reader.md), Rule 4) an edit there would
re-open its whole review loop for three added sections — a companion that cites it is the
cheaper honest shape. Nothing here changes what stage 1 of that spec shipped; everything
here layers on top of it.

## 1. The problem — three asks, one auditor's question

The maintainer's asks (2026-07-12 morning, on the record in this repository's tracker
ledger, work item `resource-accounting-spec` — run `./led show <id>` or `./led --recent`
at the repository root to read it):

1. **Count uses.** A declared resource that is *requisitioned* — acquired in discrete,
   countable acts, the way a subagent is spawned, a `claude -p` classifier call is spent,
   or a solver binary is invoked — should carry a use count. A resource that is
   *ever-present* — a standing API or service that is simply there, like the QEUBO
   backend (a preference-optimization service this maintainer runs; the registry spec's
   §1 names it as its own motivating specimen) — should carry at least a
   used / not-yet-used witness.
2. **Say when.** Each declaration should state the conditions under which the resource
   MAY, SHOULD, MUST, or MUST-NOT be reached for — a deontic register (deontic: the
   vocabulary of permission and obligation), conditioned on task shape.
3. **Type the policing.** For each resource it should be typed and queryable WHICH of
   those distinctions is actually policed, by WHAT mechanism, at WHAT grade — so a
   reader can tell an enforced MUST from an aspirational one.

The auditor's question behind all three is the same one a financial audit asks of a
purchasing ledger: what did we say we'd use, what did we actually use, and can anyone
check the difference without trusting the spender's narrative?

## 2. Two temporalities — requisitioned vs ever-present

The registry's existing CLASS field (solver | service | backend | binary | library,
[ORCH-SPEC-RESOURCE-REGISTRY.md](ORCH-SPEC-RESOURCE-REGISTRY.md) §2) already carries the
distinction implicitly; version 1 derives the accounting mode from it by a fixed, named
mapping rather than widening the declaration grammar:

- `solver`, `binary` → **REQUISITIONED**: each invocation is a countable event.
- `service`, `backend`, `library` → **EVER-PRESENT**: the accountable fact is whether it
  was reached at all (first-witnessed use, last-witnessed use), not a meaningful count.

A declaration whose reality diverges from its class's default (a metered service billed
per call, say) records that in its GUIDANCE prose for now. A typed per-declaration
ACCOUNTING column is deliberately deferred to the s27 kernel step (the `resource` ledger
kind staged in the registry spec's §8), on that spec's own principle that columns are
added when the convention has shown which ones earn their place.

## 3. The deontic register — TIER completed with `forbidden`

The existing TIER vocabulary (defined in the statement-fields list of
[ORCH-SPEC-RESOURCE-REGISTRY.md](ORCH-SPEC-RESOURCE-REGISTRY.md) §2) is already
three-quarters of a deontic register. This spec names the mapping and adds the missing
modality:

| TIER | Deontic reading |
|---|---|
| `available` | MAY — on record, no endorsement, no obligation |
| `blessed: <task-shape>` | SHOULD for that shape — reach for it or ledger one why-not row |
| `mandated: <task-shape>` | MUST for that shape — discharge is countersign-checked (§4) |
| `forbidden: <task-shape>` | MUST-NOT for that shape — **new in this spec** |

`forbidden` is one additive vocabulary value, UNBUILT at this spec's authoring — §8's
stage A is where it becomes real. That stage will add it to the TIER vocabulary the
intake validator in `bootstrap/templates/led.tmpl` teaches (the write-time grammar
refusal shipped 2026-07-12 currently accepts only the three existing tiers), will make
`bootstrap/templates/pickup.tmpl` sort it first (a prohibition outranks a mandate for a
reader's attention), and will give the eliciting preamble line its clause ("if the
task's shape matches a forbidden entry, do not reach for that tool; if you believe the
prohibition is wrong for this task, ledger a question to the commissioner — never a
silent exception"). Nothing existing is relaxed — the change is the fail-safe class
defined in [CLAUDE.md](../CLAUDE.md)'s ORCHESTRATION section.

Declined, with the reason on record: a SHOULD-NOT tier. GUIDANCE prose already carries
"when not to reach" advice, and a SHOULD-NOT strong enough to police is a `forbidden`
that hasn't admitted it yet. Two advisory registers with one policed boundary between
them would blur exactly the distinction §4 exists to type.

## 4. The policing column — derived, never self-declared

A declaration that carried its own "this is enforced" field would be an unwitnessed
claim in a typed costume. The policing status is therefore DERIVED per resource, from
two facts the deployment can check:

- **The mechanism this spec assigns to the tier**: `mandated` → countersigned
  evidence-shape review (the registry spec's §4 machinery); `blessed` → why-not-row
  visibility (audit-derived); `forbidden` → witnessed-use violation (audit-derived, §5);
  `available` → none, by design.
- **Whether that mechanism has actually run here**: a deployment whose ledger carries the
  countersign rows, or whose audit surface (§5) has been exercised, shows
  `POLICED (<mechanism>)`; a deployment that declared the tier but never ran the check
  shows `DECLARED-ONLY` — visible in the same pickup RESOURCES section as the
  declaration itself, never hidden.

The maintainer's standing proviso — appended 2026-07-12 as amendments to
[ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) and
[ADR-0013](../law/adr/0013-execution-stamina-and-structural-completeness.md) — governs
the whole column: the presence of a mechanization never licenses an
agent to treat the unmechanized text as optional. `DECLARED-ONLY` means "the text binds
and no machine has checked it yet," not "ignorable."

## 5. Usage evidence and the accounting audit

**The evidence base is the action stream** — the maintainer's 2026-07-11 principle:
guarantees rest on what the hooks witnessed, nothing else. Concretely, per deployment:
the invocation journal (`.claude/logs/invocations.jsonl`, written by the hook apparatus
around every Bash call, carrying command text, timestamps, and working directory), the
DerivationRecords the engine layer banks for solver runs (a DerivationRecord is the
solver-run provenance record — engine, version, config, input/output hashes — defined in
`engine/ledger_differential.py`; the registry spec's §4 names it as a mandated-tier
evidence shape), and the deployment's own ledger rows (why-not rows, closing rows that
cite a resource).

- **Matching is by REACH, and its denomination is named**: a use event is "a witnessed
  invocation whose command text matches the declaration's REACH field" (endpoint URL,
  binary path, venv path, or import name). Both error directions exist and are stated
  wherever counts are shown: a wrapper script hides a real use (undercount); a command
  that merely mentions an endpoint without calling it inflates (overcount). The count is
  honest about being a count of *witnessed matching events*, not a metaphysical use
  total.
- **Subagent requisition needs one new observer**: spawning a subagent is a tool call
  the hook apparatus can journal, but no costless observer for it exists yet (the
  convention to copy is the read/bash-completion observers in the apparatus registry —
  one journal line, no subprocess, no LLM call). Until that observer ships (§8 stage D),
  subagent use counts are reported UNDECIDABLE(capability_absent) — the same honest
  refusal shape the contemporaneity audit's Part 3
  ([ORCH-CONTEMPORANEITY-PART3-SPEC.md](ORCH-CONTEMPORANEITY-PART3-SPEC.md)) banked for
  its own unbuilt detection cases — never silently zero. `claude -p` spends, by
  contrast, are ordinary Bash invocations and are countable today.
- **Two surfaces.** The pickup RESOURCES section annotates each declaration in place:
  requisitioned → `uses: N witnessed, last <timestamp>`; ever-present →
  `first witnessed use <timestamp>` or the explicit `NOT-WITNESSED-USED`. The audit
  surface is `./audit --resources`, marriage-grade like every checker in this house: the
  deontic rules in ASP (Answer Set Programming, the clingo layer that is this project's
  reason to exist) — a `mandated`-shape work item closed with neither a matching use
  nor a why-not row is VIOLATED; a witnessed use matching a `forbidden` shape is
  VIOLATED; a `blessed`-shape close with neither is FLAGGED, a deliberately lesser
  verdict — with an independent SQL floor and the differential required to AGREE,
  following the conventions Part 3 (linked above) implemented: fixtures banked
  [seen-red](../GLOSSARY.md#seen-red) on both polarities, a distinct exit code,
  refusals typed.

Aggregation (the counting) is the SQL floor's natural half; the deontic verdicts (the
MUST/MUST-NOT checking) are the deductive engine's — this split is the point of the
marriage, not an implementation accident.

## 6. The financial-audit grade boundary

The maintainer's ruling of 2026-07-11 stands and this spec restates it as its own hard
edge: **hook-witnessed event counts are evidentiary; token and money figures are
diagnostic-grade, permanently.** The accounting layer emits counts and timestamps of
witnessed events. It never emits a monetary claim. An external financial process may
price the witnessed counts (N subagent spawns × the operator's known rate); the pricing
step happens outside the harness and inherits only the counts' evidentiary standing, not
a cost guarantee the harness cannot give.

## 7. Honest limits

- REACH matching is textual (§5); the error directions are named at every surface.
- History predating the instrumentation is UNDECIDABLE for counts — worlds run before a
  given observer existed report that, not zero.
- `NOT-WITNESSED-USED` means exactly that: absence of a witness is not evidence of
  non-use, and the label refuses the stronger reading by construction.
- The `forbidden` tier is audit-policed in version 1. A write-time refusal (a hook
  denying the invocation as it happens) is a possible later mechanism, out of scope
  here; declaring it in scope would promise an enforcement grade nothing in this spec
  builds.

## 8. Implementation routing (all stages Sonnet-executable from this spec)

- **Stage A — `forbidden` tier**: validator vocabulary + pickup sort + preamble clause +
  seen-red both polarities. Touches `bootstrap/templates/` — FREEZE-GATED: staged in a
  worktree and merged only when no wired session is live (run 12 is live at authoring
  time).
- **Stage B — counting floor**: the SQL usage view over journal + ledger, and the pickup
  RESOURCES annotations, with the denomination text of §5 shown at the surface.
- **Stage C — deontic checker**: the ASP program + SQL floor + differential behind
  `./audit --resources`, Part 3's conventions throughout.
- **Stage D — subagent-spawn observer**: one costless journal-line observer in the
  apparatus, registered in the mechanism registry like its read/bash siblings.
- **s27 fold-in**: when the registry spec's stage 3 lands the `resource` kernel kind,
  the ACCOUNTING column (§2) and the tier vocabulary including `forbidden` ride that
  delta; this spec adds no kernel step of its own.

Each stage carries the standing witness duties: claims WITNESSED with observed output,
REFUSED-AS-EXPECTED, or UNEXERCISED with the blocker named; fixtures registered in the
census; no umbrella claims.

## Closure statement (per [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)'s closure form)

The universe of this spec is the maintainer's three asks of §1. Ask 1 (usage counting,
split requisitioned/ever-present) is closed by §2 + §5's surfaces. Ask 2 (the
MAY/SHOULD/MUST/MUST-NOT register with task-shape conditions) is closed by §3, with
SHOULD-NOT deliberately declined and the reason recorded. Ask 3 (typed per-resource
policing) is closed by §4's derived column and §6's grade boundary. Deliberately absent,
each named where it falls: monetary claims (§6), write-time forbidden enforcement (§7),
a declared ACCOUNTING column before s27 (§2), subagent counts before stage D (§5). No
other obligations are created by this document.
