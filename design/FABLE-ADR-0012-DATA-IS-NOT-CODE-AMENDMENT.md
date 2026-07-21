# Proposed ADR-0012 amendment — "data is not code" (staged for ratification)

This document proposes an amendment to the project's structural-hygiene law,
[ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md), for the
maintainer to ratify or reject: a rule that authored content (prompt text, teaching
copy, configuration tables) must live as data files that code loads, never as
literals inside logic modules. §2 holds the exact text to append on ratification;
§1 explains the drafting choices; §3 asks the ratification question. Throughout,
"P1"/"P3"/"P9" name ADR-0012's nine numbered principles (P1 = single source of
truth: one home per fact; P3 = no god-objects), and "the ledger" is the project's
append-only Postgres decision record, written and read via the `./led` CLI.

- **Status:** DRAFT — Fable-authored 2026-07-21, awaiting maintainer ratification.
  Per the standing orchestration contract nothing in `law/` is edited until
  ratified; on ratification the block in §2 below is appended verbatim to
  `law/adr/0012-compositional-and-structural-hygiene.md`'s Amendments section
  (ADR-0005 Rule 8 dated-append form, matching the house `Amendment — <date>:
  <title>` convention).
- **Commission (verbatim, maintainer observation b):** "file size violation; factor
  out the configuration content from code #governance / 1. (ADR-0012 extension:
  data is not code; factor out the prompts)"
- **Evidence base:** the governance investigator's report — one of four read-only
  Sonnet diagnosis agents the 2026-07-21 investigation dispatched, its findings
  recorded at ledger rows 1848–1850:
  `durable_decisions.py` ~63% prose/data literals, `feature_facts.py` ~62%,
  `principals_authority.py` ~44%, `screens.py` ≥28% interleaved user-facing copy;
  no existing ADR owns data-vs-logic *location*
  ([ADR-0007](../law/adr/0007-file-size-and-information-density.md) owns file size,
  P1 owns duplication, P3 disclaims the line budget); four fresh-context ADR reviews of
  this package caught SSOT and interpreter-boundary defects and never surfaced
  the co-location, because no principle named it.

## 1. Drafting rationale (not part of the amendment text)

The line must not indict every string literal — exception messages, log lines, and
docstrings are part of the logic's own contract and belong in code. The workable
discriminator is **edit identity**: whose act is a change to this text? If its
correctness is judged by *reading it as prose or config* (teaching copy, screen
narration, a feature catalog, a rules table — the things a genericity/writing pass
edits), it is content, and content is data. If its correctness is judged by *the
code path it serves* (an error naming the invariant that failed, a log line naming
the state observed), it is code. The witnessed specimens sort cleanly under this
test: the `CATALOG`/`REGISTRY` prose blocks were literally edited by a prose
commission while living inside Python modules; the runner's error messages were not.

## 2. The amendment text (append verbatim on ratification)

*(A note on §2's citation style: the text below cites sibling ADRs by bare number —
ADR-0002, ADR-0004, ADR-0007, ADR-0011 — because its destination is ADR-0012's own
Amendments section, where those numbers sit among that document's existing linked
references; this wrapper's preface links ADR-0012 and ADR-0007 for the reader of
THIS draft.)*

---

### Amendment — 2026-07-XX: P1 extended to the content register — data is not code

*(Provenance: the 2026-07-19 setup-TUI field test and its 2026-07-21 four-class
investigation (project ledger rows 1844–1850). Witnessed substrate: three modules of
one operator-facing package carrying 44–63% authored prose/config as Python literals,
and a fourth interleaving user-facing copy sentence-by-sentence through control flow;
four fresh-context ADR reviews of that same package surfaced SSOT and
interpreter-boundary defects but never the co-location, because no principle named
it. Maintainer-instructed: "data is not code; factor out the prompts.")*

New anti-pattern row (appended, per this section's convention):

| Audit cancer / boundary | The shape to never author | Preventing rule |
| --- | --- | --- |
| **(new, content boundary)** — authored content embedded as program text | operator-facing copy, teaching prose, prompt/screen text, feature catalogs, rules/config tables, or any other content whose edits are judged by reading it as *writing or configuration*, authored as literals inside a logic module — block-form (a hundred-line dict of prose) or interleaved (copy threaded through control flow) | **P1 at the content boundary** — content has one home, and that home is a *data artifact* (a data-only module, a structured file, a keyed registry) the logic loads and renders; logic modules contain the strings that ARE logic (raised errors, log diagnostics, wire constants) and no others |

**The rule (checkable).** A file answers to one editor identity. The check: *(a) for
each sizable literal, ask whose act a change to it is — a writing/config edit, or a
logic edit; a writing-edit literal inside a logic module is the violation; (b) a
module that is majority content by volume is a data artifact wearing a logic file's
name — split it so the data artifact is declared as such and the residual logic
imports it; (c) content is addressed by key/identity from logic (the renderer
receives typed content, it does not concatenate prose fragments inline).* The
discriminator against over-reading: error messages, log lines, docstrings, SQL/wire
constants, and format strings for internal state are the logic's own contract and
stay. A one-line label does not trigger the rule; a paragraph does; between them the
edit-identity question decides, calibrated at review like P3's one-clause test.

**Why P1:** this is derive-don't-duplicate's sibling failure — not two homes for one
fact, but one home serving two masters. Co-located content defeats both audiences at
once: the prose reviewer cannot see the copy as a document (it is shredded across
call sites), and the code reviewer wades through pages that carry no decisions
(ADR-0007's density red flag), while every content edit shows up as a *logic diff*,
maximizing partial-visibility hazard (ADR-0004) for zero-logic changes. It also
composes with this tenet's existing "Amendment — 2026-07-18: The interpreter
boundary — a value never crosses as program text": content rendered by
interpolation into program-adjacent text is one refactor away from the very
splicing that amendment bans (a value concatenated into text a second evaluator
parses, able to alter the utterance's structure), whereas content addressed as
typed data is not.

**Cancer prevented:** the content-register form of **B** (a logic file becomes the
second, unacknowledged home of what is really a document), of **G** (load-bearing
operator guidance living where no writing review will ever read it), and the
root cause of chronic ADR-0007 violation in operator-facing modules (the witnessed
substrate: files at 1.2–3.6× the ceiling whose overage was majority content).

*Enforcement surface (ADR-0011 Rule 1, honest): review-only at authoring — the
edit-identity question is a judgment; the max-lines gate (ADR-0007's mechanization,
minted from this same field test) is the blunt backstop that forces the question at
the moment a file grows past budget. The ADR-0011 Rule-2 trigger: if a
majority-content logic module recurs after this record, mint the measured check (a
literal-volume-fraction lint over the affected package) rather than re-stating the
rule in prose. No retroactive sweep: the witnessed offenders are already queued under
their own remediation track; existing files elsewhere retrofit on touch (ADR-0004).*

---

## 3. Ratification question for the maintainer

Ratify §2 as written for append to ADR-0012's Amendments (with the date filled at
ratification), or return with edits. One deliberate scoping choice to confirm: the
rule is filed under **P1 (one home)** rather than as a tenth principle, because the
existing amendment machinery (anti-pattern row + dated rule) carries it without
renumbering the nine — flag if you want it as **P10** instead.
