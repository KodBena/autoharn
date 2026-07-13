# Decision brief — may the engine ever refuse a write?

*For the maintainer. One decision, three options, plain language. Everything here is
context; nothing is committed until you rule. A second, smaller pending ruling is at the
end — it can wait.*

## The question in one paragraph

The harness already refuses some dishonest writes at the moment they happen — the stamp
gate that caught e17's fake "independent review" is one, built by hand as kernel
machinery. The deductive engine now being designed will *derive* judgments like that
mechanically, in quantity. The question: **may the engine's judgments ever be turned into
refusals, or must the engine only ever watch and report?** The ratified architecture
document (the "marriage" doc) currently says the engine layer never enforces — "the only
deny surfaces remain the write-boundary triggers… not this design's to touch." One panel
design built a pipeline whose entire purpose is promoting proven engine judgments into
refusals; another assumed the engine never denies. They cannot all be right, and the
project's own letter-vs-spirit rule says a redraw of a ratified line must be brought to
you, not folded in quietly.

## Option A — the engine never denies (strict watch-only)

The marriage line stands untouched. Refusal gates like e17's can still exist, but each
one is hand-built kernel machinery, individually designed, with the engine having no
role in creating them.

- **You get:** zero risk that a wrong mechanical derivation ever blocks honest work.
  The simplest safety story to explain to an outside inspector.
- **You give up:** the "measure once, then mechanize" posture you ruled after e16 loses
  its mechanized half — every new gate for a known dishonesty class is a bespoke build,
  and gates will lag behind what the engine already knows. Continued sloppiness gets
  measured instead of stopped, which is what that ruling rejected.

## Option B — promotion, but every single deny is ratified by you (recommended)

Watch-only is the DEFAULT; the marriage line stays as the default. A specific judgment
may be promoted into a refusal only when four things exist, per judgment: (1) a captured
real specimen of the dishonesty it stops; (2) a PROOF that the quick write-time check
answers exactly as the full engine would — the panel's refuters showed that without this,
you can get a refusal the engine itself later contradicts, which teaches subjects to
distrust and evade the gates; (3) a teaching message naming the honest alternative
(e17's lesson: a refusal that teaches converts; one that just blocks corrodes); (4) your
ratification, one judgment at a time. The e17 stamp gate already followed exactly this
path, so the template is proven, not hypothetical.

- **You get:** the mechanization pipeline exists AND the strongest safety argument —
  nothing refuses honest work that you didn't personally examine once.
- **You give up:** speed. Every promotion waits on you. Given the promotion rate is
  likely a few per era, not per week, this cost looks small.
- **Also entails:** the marriage document gets a recorded amendment (the redraw is
  ratified rather than silent).

## Option C — promotion by checklist, no per-judgment ruling

Once a judgment passes the criteria list, it may be compiled into a refusal without an
individual ruling.

- **You get:** the fastest path to mechanized enforcement.
- **Why I recommend against it:** the panel's refuters demonstrated that the two most
  load-bearing checklist items are NOT mechanical — the flagship design misclassified a
  judgment on its own example list, in public, while claiming the classification was
  purely syntactic. A checklist known to require judgment, run without a judge,
  delegates the refuse-honest-work risk to nobody.

## What a wrong choice costs, both directions

Too strict (A): known dishonesty classes stay measured-not-stopped; the record fills
with adjudication work a gate could have prevented. Too loose (C): one wrong refusal of
honest work, delivered with a confident teaching message, is the most corrosive artifact
this system can produce — it teaches the subject that the gates lie.

**Recommendation: B.** It is also what tonight's own history looks like — e17's gate was
specimen-backed, equivalence-trivial, teaching, and ratified. Option B just makes that
story the law.

---

## The second pending ruling (smaller; can wait; no build blocked on it)

**How long do we keep the stamp secret?** The HMAC stamps that make row provenance
verifiable depend on a secret. Keep it forever → an inspector decades later can
re-verify every stamp, but the secret's secrecy — the thing that makes stamps mean
anything — must then survive forever too. Destroy it at run end → stamps become
"verified at the time, trust the record of that" — nobody can ever re-check.
Middle path, which I lean toward: one fresh secret per run, retained afterwards in a
sealed store where every access is itself a logged event, with the whole arrangement
declared in the conformance honesty sheet. Rule whenever convenient; nothing this month
depends on it.
