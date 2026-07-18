# AUDITOR — fire up a second opinion on a snag

<!-- doc-attest-exempt: doc-tree relocation mechanical edit (work item doc-tree-reorg-user-guide, ledger row 1620, 2026-07-18) -- relative link path(s) repointed to a sibling file's new location after a git-mv relocation elsewhere in the tree; no prose rewrite, same disposition as the v1.1.2 release-cut's own markers (commit 543a389). Removal condition: strike this marker and run the real A:B:C loop next time this file is touched for content, not just link repair. -->


The affordance ADR-0014 names: when a problem *resists resolution* — two attempts have addressed
the wrong target, a diagnosis keeps proving partial, or a fix "feels" right but you cannot see the
type that would dissolve the class — you do not grind a third attempt inside the same frame. You
fetch an **independent, deliberately un-led second pair of eyes**. This file is how, in this repo.

## When (the observable trigger — not a feeling)

Invoke on an *observable recurrence*, because the faculty that would feel stuck is the one that is
locked (ADR-0014 Rule 2):

- ≥2 attempts that each turned out to address the wrong target;
- a diagnosis that keeps proving partial (each fix moves the symptom, never resolves it);
- growing thrash (attempts getting longer / more speculative without converging);
- or: you cannot see the *type/shape* that forecloses the whole defect class (ADR-0000) — that
  blindness is itself the trigger.

Do **not** invoke reflexively at the first friction (that is the offload-reflex Rule 1 forbids).
Think first; notice the recurrence; then ask.

## How (brief for INDEPENDENCE — do not lead the witness)

The entire value is that the second opinion has not walked your path. So:

1. **Give the problem and the evidence** — the symptom, the measurements, what was observed — the
   same facts you reasoned from.
2. **Do NOT pre-lead it** with your diagnosis, your frame, or your list of suspects. "Find the bug I
   missed in X" reproduces your lock in the second agent — your one frame, run twice.
3. **Invite reframing.** The highest-value output it can give is "this is not that kind of problem
   at all"; a leading brief makes that unsayable.
4. **Record it verbatim** (ADR-0005 Rule 9): the commission prompt and the report are the artifact.
   In this repo, an out-of-frame review is an Agent-tool subagent; its prompt + output are the record.

## What it is for (ADR-0000)

Most often the second opinion is fetched to find the **type that forecloses a class** — the
signature, the seam, the structural invariant that makes the bug unrepresentable. A class you keep
patching instance-by-instance is usually a type you have not yet seen. The auditor supplies the
frame in which that type becomes visible.

## You still own the result (ADR-0014 Rule 4 / ADR-0013 Rule 5)

A second opinion is a **hypothesis to integrate with judgment**, never a verdict to rubber-stamp
(rubber-stamping is ego-locking one step downstream). Verify its proposed fix against the symptom
the two prior attempts failed to resolve — the artifact, not the claim.

## The standing negative-register instance

The project's **hack-rationalization detector** is the same move aimed the other way: an
independent subagent run on a *justification-as-suspect* (is this "minimal / right-scope / done" a
real disposition or a rationalized corner?). Reach for it whenever a fix is about to be called
"fixed" and a slot/field/state has more than one writer. Give it the diff and the claim, not your
verdict.
