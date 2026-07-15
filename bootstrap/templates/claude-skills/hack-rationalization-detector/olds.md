---
name: hack-rationalization-detector
description: >
  Adversarial review pass that catches a fix being a hack while it is dressed
  as discipline. Use this whenever a change is about to be called "fixed",
  "done", "minimal", or "the right scope"; whenever reviewing a PR, diff,
  commit, or refactor for laziness; whenever an "independent" or "non-lazy"
  review is requested; or whenever a fix touches a slot/field/state that has
  more than one writer. Run it EVEN IF the change has green tests and an
  approving review — green tests and a same-frame approval are exactly the
  conditions this pass exists to distrust. Do not skip it because the diff
  looks small or locally reasonable; "locally reasonable" is the disguise.
---

# Hack Rationalization Detector

## What this is, and the one rule that makes it work

This pass catches a specific, recurring failure: a change that is *behaviorally
correct and locally reasonable* but *structurally a hack* — and that has been
talked into looking like discipline ("minimal", "proportionate", "don't
over-engineer", "out of scope"). The failure is not low effort. It routinely
arrives after long, earnest work and a fluent justification. Effort is not the
signal. The signal is a **named-better-fix that got downgraded**, and a
**generalization that was skipped**.

**The rule: run this OUT OF FRAME.** A rationalization cannot audit itself.
If you wrote the diff and the justification, you are the wrong agent to run
this — you will read your own reasoning, agree with it, and pass. This is the
exact way an "independent" review fails: it inherits the implementer's framing
and only confirms "the solution matches the stated problem", never discovering
that the stated problem was wrong.

So one of these must hold before you proceed:
- You are a separate invocation / subagent that did **not** produce the change
  and has **not** seen the implementer's reasoning, OR
- You have the implementer's justification in front of you and you are treating
  it as **the object of suspicion**, not as context to agree with.

If neither holds, stop and say so. A self-applied run of this skill is theater.

## What you produce

You do **not** render a tasteful verdict on whether the code is "good". That is
not mechanizable and you will only launder your own taste. Your job is to force
one artifact to the surface that the implementer's process lets stay invisible:

```
GENERAL FIX:   <the most general correct fix, stated as a one-sentence invariant>
PATCH SHIPPED: <what the change actually does>
DOWNGRADE:     <why the patch was chosen over the general fix — quote the words used>
VERDICT:       general | narrower-but-justified | UNDISCHARGED-HACK
WRITER DELTA:  <claimed writers> vs <independently enumerated writers>
```

`UNDISCHARGED-HACK` is the finding when a more-general fix was identifiable and
was set aside using minimality language without a concrete cost that justifies
the narrowing. That is the precise shape of the documented failures — see
`references/known-cases.md`. Read it before judging; it is your few-shot.

## Procedure

Work in this order. The first two steps are deterministic scripts — run them,
do not eyeball. They bite because they cannot be reasoned around.

### Step 1 — Scan the justification for the laundering signature

Run the tells scanner over the change's prose (PR description, commit message,
the implementer's explanation, inline comments in the diff):

```bash
python scripts/grep_tells.py <path-to-justification-or-diff>
# or: git show <sha> | python scripts/grep_tells.py -
```

It flags minimality-words ("scope creep", "over-engineer", "proportionate",
"minimal", "for now", "out of scope", "follow-up") that occur near a *named
alternative fix* ("the deeper fix", "the right fix would be", "we could
instead", "owner/ownership", "the general case"). A hit is not proof. A hit is
the place to look: it is where a better fix was named and then argued down. In
the worst documented case the implementer literally wrote the correct fix one
sentence before discarding it. The scanner finds that sentence.

For every hit, demand the DOWNGRADE line: what concrete cost justified choosing
the narrower fix? "Minimality" is not a cost. "Proportionate" is not a cost.
A real cost is "the general fix requires touching a partially-visible file I
can't see all of" (ADR-0004-shaped) or "it changes a public contract mid-sweep".
If the only stated reason is a discipline-word, the verdict is
`UNDISCHARGED-HACK`.

### Step 2 — Independently enumerate the writers

Most hacks in this codebase are *failures to generalize across producers*: a
per-writer gate added when N writers exist and only some were enumerated. Do
not trust the change's count of who writes the touched state. Re-derive it from
the code yourself:

```bash
python scripts/enumerate_writers.py <symbol-or-field> <source-root>
# e.g. python scripts/enumerate_writers.py cardTree frontend/src
```

It lists candidate write-sites for the symbol. It over- and under-includes —
it is grep, not a type-checker — so read the hits, don't just count them. The
value is that the count now comes from the code, not from the implementer's
memory. Compare against the writers the change *assumed*. A mismatch (the
documented case enumerated two writers when three existed) is a load-bearing
finding: a per-writer gate is fragile exactly because it fixes producers one at
a time, and the missed producer is where the bug survives. Put the comparison
in the WRITER DELTA line.

If there is more than one writer and the fix gates per-writer rather than
establishing a single invariant over all writers, that is a strong
`UNDISCHARGED-HACK` signal even if every currently-known writer is handled —
because the next writer added will reopen it.

### Step 3 — The judge pass (held to forcing the artifact, not to a verdict)

Now, and only now, read `references/known-cases.md` and ask whether this change
rhymes with either documented case. You are looking for the signature, not
grading aesthetics:

- Was a more-general fix *named* anywhere in the reasoning and then set aside?
- Is the fix a set of example-cases ("handle A, handle B...") where a single
  property would have covered all cases ("a clearer only clears what it owns")?
  If you cannot state the fix as one invariant that quantifies over all
  producers, the change is N patches, not a fix.
- Did the change inherit a *frame* ("this is a review-vs-browse bug") that the
  evidence does not actually support ("it was a slot-ownership bug all along")?

The judge is the soft part of this skill and it is gameable — an implementer can
learn to stop writing the admission. So do not let the judge produce a verdict
on its own. Its output is to **force the GENERAL-FIX / PATCH / DOWNGRADE lines
to be filled in concretely**. A change that cannot articulate its own
general-fix-and-why in three honest lines has not earned "done", whatever the
test suite says.

### Step 4 — Runtime, if the claim is "fixed"

If the change is being called *fixed* (not just *reviewed*), confirm the failure
was reproduced and the fix verified against the running software — not derived
on paper. Green tests on a wrong model are worse than no tests: they manufacture
the confidence that lets a same-frame review approve. "Verification is runtime
observation" — if no repro exists, the verdict is not "looks fixed", it is
"unverified".

## Output template — use exactly this

```
## Hack-rationalization review: <change id>

FRAME CHECK: <out-of-frame? or justification-as-suspect? — if neither, STOP>

GENERAL FIX:   <one-sentence invariant, or "could not be stated as one invariant">
PATCH SHIPPED: <what it does>
DOWNGRADE:     <the concrete cost that justified narrowing, or the discipline-word used in its place>
WRITER DELTA:  <claimed> vs <enumerated>  (writers: <list>)
RUNTIME:       <reproduced + verified | unverified — derived on paper>

TELLS (Step 1): <hits, file:line + the named-then-downgraded sentence>

VERDICT: general | narrower-but-justified | UNDISCHARGED-HACK
WHY: <2-3 sentences, no discipline-words used as reasons>
```

## What this pass does NOT do (state it, don't pretend otherwise)

- It does not detect a *novel, working, general-but-ugly* hack. There is no gate
  for taste. This pass catches the documented failure — *named-and-bypassed* and
  *failed-to-generalize* — which is where the evidence is, and nothing more.
- The Step 3 judge is gameable by an implementer who stops narrating. The
  durable parts are the two scripts and the forced GENERAL/PATCH/DOWNGRADE
  artifact, which is checkable even when the prose is clean.
- A clean run is not absolution. It means the two known shapes are absent, not
  that the change is correct.
