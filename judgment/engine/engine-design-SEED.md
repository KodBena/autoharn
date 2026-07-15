# Deductive-engine design SEED — panel synthesis (Fable main loop, session `7be3443d`, 2026-07-07)

**Status: SEED, not a commission.** The engine remains the project's Fable-reserved
endpoint; this seed exists so that work can RESUME from a banked position — by stand-ins
for the mechanical slices marked so, by renewed Fable access for the parts marked
elevate-only-on-Fable. Anchor this file's sha256 into acts.ruling at commit.

## Provenance (read before trusting anything below)

Produced by a structured panel (workflow `wf_1ae3bf30-850`, ~1.04M tokens): four
independent designers on disjoint lenses (semantics / architecture / evaluation /
adversarial), one adversarial refuter per design, one completeness critic over the set.
All nine invocations self-reported `claude-fable-5` (each honestly noting it has no
introspective channel to detect silent substitution). Verbatim outputs are committed at
`consults/engine-panel/` — this synthesis CITES them; it does not replace them. My own
shape was committed BEFORE the panel launched
(`claude_harness/docs/design-notes/deductive-engine-fable-main-shape.md`) and no brief
contained it — commit order proves the independence. **Common-mode disclosure (critic
§3):** designs AND refutations share one model; each refuter read only its own lens;
cross-design contradictions were structurally invisible to the process and were caught
only by the critic pass — and model-level blind spots are shared by construction. A
future non-Fable review of this seed is therefore worth having, not a formality.

## Convergence check against the pre-committed shape

All five pre-committed commitments were independently re-derived by panelists who had
not seen them: (1) replay/specimen ground truth — the evaluation lens built a three-tier
ground-truth taxonomy on the banked corpus unprompted; (2) assign-don't-compete with a
two-producer differential — upheld by every lens; (3) the compilation seam as THE
research question — the architecture lens made it the promotion ladder (P0–P5); (4)
law-cited derivations — the semantics lens made the law term type-mandatory; (5)
engine-under-BRIEF — the adversarial lens's entire frame. Convergence is encouraging but
carries the common-mode caveat above.

## The load-bearing survivors (attack-tested; cite the salvage sections)

- **The judgment type** (family, verdict, subject, law, frontier) + DerivationRecord-or-
  NO-RESULT — AMENDED per refutation: a SIXTH component, the evaluation clock, pinned
  and hash-covered (expiry judgments are functions of (frontier, now); replay breaks
  without it).
- **Per-family closed verdict enums, no global truth lattice**, aggregation at declared
  mappings only — AMENDED: every family carries a non-run/QUARANTINED member (the
  semantics design claimed this and its own table violated it, six families lacking one).
- **The deontic architecture**: no modal operators; obligation = recorded other-assigned
  fact; the engine derives DISCHARGE STATUS only; violation is a routed flag (F28
  intact). The strongest attacked-and-standing section in the panel.
- **Quotational paraconsistency**: atoms are facts ABOUT assertions; record-contradiction
  is data, never theory-inconsistency; FDE confined to report side.
- **Prefix-determinedness**: append-only + backward edges + id-is-order makes correctly-
  classified judgments tier-invariant — CONDITIONAL on a MECHANICAL class checker (the
  flagship design misclassified `launder` on its own list; hand classification is
  disqualified by specimen).
- **P3, the best single rule in the panel**: a gate must verify the claim against an
  invariant witness the writer does not control — never price a self-declared label.
  (Honestly non-mechanical; stop advertising it as mechanical.)
- **Three-tier ground truth + append-only expectations ledger** — AMENDED: no automatic
  re-keying ever (that is F28's auto-resolve one level up); SUPERSEDED flags and blocks
  green until a human re-keys. Tier-1 carries a birth-independence caveat (both producers
  authored by one mind in one session; AGREE banks shared misreadings).
- **The threat catalog L1–L10** (how engines lie) as the organizing register — with
  "kills" demoted to "bounds" wherever the mechanism bottoms out in fixture coverage.
- **DerivationRecord + watermark self-citation currency** — the one countermeasure whose
  "kill" header held under attack.
- **UNPROVEN-NET as a display property** (ADR-0011 applied to the reader) — pinned to
  (judgment, rule-hash, engine-version).
- **The admission protocol** (law + banked specimen + flipping mutation + justified
  assignment + declared mode ceiling) and a first-class NON-DERIVABILITY register.

## Binding amendments from the refutations (none optional at elevation)

Clock-in-the-type; per-family non-run members; promotion criterion (i) upgraded from
budget to PROVEN VERDICT-EQUIVALENCE (delta-closure ≡ full-frontier, per judgment —
write-time refusal contradicted by the engine's own turn-time derivation is the most
corrosive artifact this design can emit); a workable refusal-capture mechanism with a
stated atomicity story and second witness (RAISE EXCEPTION rolls back same-transaction
journal inserts — the naive journal is empty by construction); a stated HMAC-secret
retention/re-derivation policy (retain → the tripwire limit widens to forever; discard →
stamp_verified is trust-me forever; this is a genuine dilemma needing a maintainer
ruling, not a design dodge); an independence-preservation bound on codegen (generate at
most N−1 of N encodings — the F-A `answered` twin-blindness is the banked specimen);
DIVERGE_BY_DESIGN requires independent ratification (the mover never licenses their own
flip — pilot-F7); per-rule grounding witnesses or clingo-warnings-promoted-to-RED (an
unmatched body predicate is a legal empty relation — the pilot-light atom guards the
already-guarded case); an append-only regold protocol with contest records; a
review-queue debt close line (open/aging unadjudicated flags — a green close over
hundreds of unread flags is the dressed-up-QED at system level); the machine-readable
law census with ratification-depth marking SEQUENCED BEFORE any constructor refusal;
G5-class cross-stream ordering is BLOCKED until solved — the critic's `acts_live`
shared-id-sequence observation is the most promising dissolution and deserves first
attention at elevation.

## The critic's structural mandates (whole-panel gaps)

1. **Increment 0 is UNIFICATION, and someone must own it:** four designs minted four
   registries, four verdict vocabularies (QUARANTINED means four subtly different
   things), four names for the frontier, four build orders. One authority module, one
   vocabulary, one merged increment plan — before any content increment.
2. **The deny-surface question needs a MAINTAINER RULING before increment 1:** the
   marriage's §8 line ("no enforcement from the engine layer") vs the promotion pipeline
   is a real redraw, three designs silently disagree, and per the letter-vs-spirit rule
   the divergence is surfaced, not folded in. (My recommendation, pre-banked: keep the
   marriage line as the DEFAULT; every promotion to a deny surface is a per-judgment
   maintainer ratification with verdict-equivalence proof attached — the e17 stamp gate
   as the template. But the ruling is the maintainer's.)
3. **Cross-session obligations:** the BRIEF's central obligation shape (approval in one
   session, discharge in another) is unrepresentable in every design as written;
   session-scoped grounding vs lifecycle-scoped obligations must be reconciled at
   elevation (open-obligation carry-over state, or lifecycle grounding units).
4. **Wire the adjudication loop to the EXISTING surface** (`experiments/adjudicate/`,
   schema-first HITL) — no design remembered it; flags need a designed landing place,
   id/frontier semantics, and re-derivation churn rules.
5. **Law epochs:** retroactivity semantics for newly ratified laws over pre-law records
   (they cannot satisfy stamp-distinctness predating stamps); capability manifests cover
   absent fact families, not absent law eras.
6. **Armed-state specimen provenance:** post-arming organic specimens come from a
   subject+engine system; fixtures must carry the apparatus configuration they arose
   under; re-baselining is owned work.
7. **The unowned BRIEF items:** F10 conservative-abstraction argument for the ids-not-
   text gap; F12 assurance-case argument structure (green lines → honest record is an
   ARGUMENT, not a talisman); F13/I11 decades-scale retention incl. archived solver
   versions; G12 access events; G14 explicit security scope declaration; Part-11 trusted
   clock. Each gets an owner or a declared exclusion at elevation — silence is the one
   forbidden state.

## Division of labor going forward

**Elevate-only-on-Fable (or better):** increment 0 unification; cross-stream frontier
semantics (the acts_live dissolution); the deny-surface ruling support; the F10/F12
arguments; any new `.lp` authoring (marriage §10's solver-file degradation hazard —
who writes solver text safely is an OPERATIONAL constraint, noted by the critic).
**Stand-in buildable against this seed + the panel files:** the mechanical class
checker; registry mechanics once increment 0 lands; per-rule grounding witnesses;
close lines (review-queue debt, latency with honest instrumentation); the law census
extraction; fixture/mutation infrastructure; the refusal-journal mechanism ONCE its
design is ruled. **Maintainer:** the deny-surface ruling; the secret-retention dilemma;
DIVERGE_BY_DESIGN licensing authority.

The panel files are the design; this seed is the map. Elevation begins at increment 0,
not at content.
