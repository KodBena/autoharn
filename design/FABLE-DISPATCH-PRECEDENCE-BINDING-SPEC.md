# FABLE-DISPATCH-PRECEDENCE-BINDING-SPEC — binding agent dispatch to the s39 start-gate

<!-- doc-attest-exempt: commissioned spec, frozen 2026-08-06 pending maintainer ratification
(commission rows 1083; provenance rows 1066/1084). Removal condition: superseded by the
implementation's completion record or a ratified live edition. -->

Fable-authored 2026-08-06. Commission: the maintainer's 2026-08-06 instruction ("dispatch-time
precedence refusal and typed annulment is something I'd ask you to do right away, and schedule
their implementation"), ledger row 1083. Provenance: work item dispatch-time-precedence-refusal
(row 1066, gui-spy-3 report leg 1), the maintainer's own witnessed pain 2026-08-04, verbatim:
"I once again encountered a problem with one of the orchestrators starting an agent in the
wrong order, and so violated precedence constraints."

## 1. The corrected premise (row 1084)

Row 1066 asked whether the kernel wants a start-time refusal primitive. It already has one,
and has since 2026-07-17: `kernel/lineage/s39-blocks-start.sql` provides

- the `blocks-start` edge value on `work_depends_on` (antecedent must reach CLOSED before the
  dependent may be CLAIMED), disjoint from `blocks-close` (gates close only, deliberately) and
  `informs` (never gates, deliberately);
- construction-time refusals (self-edge, dangling antecedent, cycle over the blocks-start
  subgraph, independent of the blocks-close subgraph by s39's own defended design choice);
- a claim-time refusal on `work_claimed` INSERT naming every unresolved antecedent and the
  honest next acts;
- the `work_startable` view: open, unclaimed items whose blocks-start antecedents are all
  closed — "what can I legitimately claim right now";
- defense-in-depth `blocks_start_cycle` members in both violation views.

s39 is in `LINEAGE_CHAIN`, live in autoharn3, and live in experience4's kernel since their
2026-07-27 birth. The panel's three witnessed precedence violations happened WITH the primitive
present: the orderings were never declared as blocks-start edges, and agents were spawned
without claims. This spec therefore adds NO kernel delta. Its whole subject is the binding
layer — the gap between the primitive and practice.

## 2. The binding rules (normative on ratification)

**R1 — Declare start-order as blocks-start at commission time.** When an orchestrator opens
work items whose START order matters (not merely their close order), the ordering is written as
`blocks-start` edges at open time. `blocks-close` states a close obligation and licenses
concurrent starts by design; writing it (or nothing) where start order matters is the defect
family the panel hit. Named consumer of every such edge: s39's claim-time refusal — an edge
nobody would ever claim against fails the named-consumer test and is not written.

**R2 — Claim before dispatch.** No implementer/builder agent is spawned for a work item the
dispatching principal has not first claimed. The claim is the mechanical dispatch-time gate:
the kernel refuses it while any blocks-start antecedent is unclosed, which makes the refusal
fire at the moment that matters — before work begins — with no new mechanism. Dispatches that
carry no work item (consult legs, spies, read-only reviews) are the disclosed exception; they
cannot violate item precedence by construction, and they stay item-free honestly rather than
claiming a decorative item.

**R3 — Dispatch from the startable read.** When choosing what to dispatch next, the orchestrator
reads `./autoharn led work startable` (or a mandated scheduler that itself reads it), never a
hand-held mental order. Hand-scheduling over a mandated scheduler is the violation family
twice maintainer-caught on the panel.

**R4 — Teach where the violation happens.** The s39 claim refusal already teaches. The docs
half: ORCH-CAPABILITIES.md gains the R1–R3 binding (orchestrator-facing), and the GLOSSARY's
precedence entries state plainly that blocks-close does not gate starting and what does. Every
doc example carries witnessed output per the standing claims-carry-witnesses rule.

**R5 — Answer missive to experience4.** Their pain is answerable today: one missive on the
originating thread stating that s39 is live in their kernel since birth, with the R1–R3 recipe.
Sent after the docs leg lands, citing it.

Out of scope, named: a PreToolUse hook mechanically refusing agent spawns for unclaimed items.
It is the natural third enforcement layer, but it touches hooks/ (live-session merge hold,
durable row 263) and its trigger condition (mapping a spawn to a work item) has no reliable
observable today; it is a named empty slot, re-openable if R1–R3 practice fails again — a
recurrence past spec and review is ADR-0011 grounds for a mechanism.

## 3. Implementation schedule

One Sonnet leg (docs + missive + ledger corrections), serialized after the in-flight B1 build
(shared docs surface). No kernel build, no birth-chain entry, no scratch witness needed — the
witnessed-output rule on doc examples is the leg's witness obligation. The row-1066 item closes
on the leg's commit, citing row 1084's correction; the gui-spy-3 report is NOT edited (point-
in-time record) — the correction lives in the ledger and in this spec's §1.
