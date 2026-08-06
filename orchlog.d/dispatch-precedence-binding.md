subject: e8582be9
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

**The correction, stated plainly because it is the whole point of this note.** The maintainer's
2026-08-04 pain ("I once again encountered a problem with one of the orchestrators starting an
agent in the wrong order") read at first as a missing kernel primitive. It was not: the kernel
has carried a start-time precondition primitive since **2026-07-17**
(`kernel/lineage/s39-blocks-start.sql`, see the pre-existing
[`orchlog.d/s39-blocks-start-panel.md`](s39-blocks-start-panel.md)
note) — live in autoharn3 and in every world scaffolded since. The panel's witnessed precedence
violations happened WITH s39 already present in the schema: the orderings were never declared as
`blocks-start` edges, and agents were spawned without a prior claim.
[design/FABLE-DISPATCH-PRECEDENCE-BINDING-SPEC.md](../design/FABLE-DISPATCH-PRECEDENCE-BINDING-SPEC.md)
(maintainer-ratified 2026-08-06, row 1087) therefore
adds NO kernel delta — its whole subject is binding PRACTICE to what the kernel already offered.

**The three binding rules ([ORCH-CAPABILITIES.md](../ORCH-CAPABILITIES.md)'s item 48 has the full
text and a witnessed both-polarity transcript):** R1 — declare start-order as `blocks-start` at commission time
(`blocks-close` deliberately licenses concurrent starts; writing it, or nothing, where start
order matters is the defect family that hit the panel). R2 — claim before dispatch: never spawn
an implementer for a work item you haven't first claimed; the claim IS the dispatch-time gate,
refused by the kernel while any `blocks-start` antecedent is open. R3 — dispatch from `./autoharn
led work startable`, never a hand-held mental order.

Named limit: s39 checks DIRECT antecedents only, not a transitive chain. Named out-of-scope: a
PreToolUse hook mechanically refusing an unclaimed-item spawn — the natural third enforcement
layer, not built (touches `hooks/`, live-session merge hold; re-openable per [ADR-0011](../law/adr/0011-mechanization-discipline.md) if R1–R3
practice fails again).
