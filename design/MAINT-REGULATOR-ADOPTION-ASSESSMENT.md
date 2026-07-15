# Regulator-adoption assessment — four institutional lenses on autoharn, 2026-07-12

<!-- doc-attest-exempt: v1.1.3 release-cut mechanical edit (de-linked dangling references into paths excluded from this public cut -- observatory/, research/foundational-map/, design/MAINT-PG-HBA-HARDENING.md -- plain-text citation, no prose rewrite), same disposition as the v1.0/v1.1/v1.1.1/v1.1.2 cuts' own markers on their touched files. Removal condition: strike this marker and run the real A:B:C loop next time this file is touched for content, not just link repair. -->

Audience: maintainer

This document answers one maintainer-commissioned question: **if institutions with the
expectations of the NRC (nuclear high assurance), NIST (standards and controls), the FAA
(aviation software assurance, DO-178C-shaped), or a demanding tribunal ("ICJ", read as the
evidentiary standard a hostile forensic examiner applies) looked at autoharn today, could
they adopt it for software development with Claude — and if not, precisely why not?** It is
written for the maintainer as planning input ("we'll use it to plan ahead how to proceed"),
and it also answers the commission's second question: what does
[the BRIEF conformance map](../law/briefs/BRIEF-CONFORMANCE-MAP.md) — the project's standing
self-assessment against its own safety-critical-logging
[BRIEF](../law/briefs/safety-critical-logging/BRIEF.md) — never ask at all, because the gap
is in the map's own frame rather than in an unfilled row?

**The honesty constraint is stated before anything else and governs every line below.** The
four institutional assessments in this document were produced by Sonnet-class analyst agents
reasoning in a regulator's *frame*. That is a LENS for finding gaps — it is not a
certification, not a legal opinion, not a compliance determination, and no simulated verdict
here carries any regulator's authority. This is the project's own axiom applied to itself:
no LLM judgment sits in a verdict path (BACKLOG.md entry "Two ratifications (maintainer,
2026-07-11 evening)", ratification 1's sub-question 2). Every verdict below is advisory
input for planning, nothing more. Where this document says "not-yet", it means "a gap
inventory taken in that institution's frame found blocking items", never "an authority has
ruled".

## Method, and how to re-check any claim

Four analyst agents were commissioned per the standing delegation contract
([CLAUDE.md](../CLAUDE.md) ORCHESTRATION), one per lens, each self-contained: each read the
governing documents ([OPERATING-CARD.md](../ORCH-OPERATING-CARD.md),
[CAPABILITIES.md](../ORCH-CAPABILITIES.md), the conformance map and BRIEF above, the
[kernel lineage](../kernel/lineage/), the [hooks](../hooks/), the
[seen-red](../GLOSSARY.md#seen-red) corpus, [BACKLOG.md](../BACKLOG.md)'s dated 2026-07-11
tail) and, where load-bearing, queried the settled [worlds](../GLOSSARY.md#world) read-only
over psql. Their reports are session working input, not banked artifacts; therefore **every
claim carried into this document points at a repository artifact or a named live
observation, re-verifiable without the reports** — and the live observations marked
"verified 2026-07-12" below were re-observed directly by the synthesizing session, not
taken from any agent's summary (the standing rule: verify artifacts, never reports).

The live observations this document leans on, each re-verified 2026-07-12:

- `git tag -l` returns zero tags — no `ratified/*` tag exists.
- `law/keys/` contains only [README.md](../law/keys/README.md) (its own AWAITING-KEY stub);
  no public key has ever been committed.
- `SELECT column_name FROM information_schema.columns WHERE table_schema='run11' AND
  table_name='ledger' AND column_name='row_hash'` against the toy db returns zero rows —
  the newest settled world has no hash chain; s26 postdates every existing world.
- `SELECT rolname, rolpassword IS NOT NULL, rolsuper FROM pg_authid WHERE rolname='bork'`
  returns `bork|f|t`, and `SHOW ssl` returns `off` — a passwordless superuser reachable
  over the network, TLS off, exactly the state
  design/PG-HBA-HARDENING.md (the maintainer-internal pg_hba hardening write-up, not part of this public release) was written to close and whose status
  is still prepared-unapplied (also CAPABILITIES.md "Not yet enforced").
- No `requirements.txt` or `pyproject.toml` exists at the repository's top two levels — the
  apparatus has no dependency manifest.

## The four verdicts

All four lenses returned **not-yet**, and — the load-bearing observation for planning —
they converge on the *same small set* of blockers rather than four disjoint lists. One line
each, in the register the honesty constraint requires:

| Lens | Advisory verdict | The one-line why |
|---|---|---|
| NRC (nuclear high assurance) | not-yet | Architecture unusually well-aimed and candid, but the outside-the-host evidence layer is unarmed, independence never leaves one host/vendor/human, contemporaneity is self-documented as violated in practice, and the Postgres substrate has no survival story. |
| NIST (controls) | not-yet | A genuinely strong, self-critical ledger core inside an open perimeter: passwordless network superuser with TLS off, keyless crypto layer, no backup, no dependency manifest. |
| FAA (DO-178C-shaped) | not-yet | Real credit on attributability, immutability, and solver provenance — but no configuration index pins which apparatus version governed which world, traceability's gap-detection half is unbuilt, and the verifier itself is unqualified and untested. |
| ICJ (evidentiary) | not-yet | The tamper-evidence mechanism is real and well-engineered but currently protects zero bytes of the evidence that exists; pre-s26 custody rests on a ruling, not a mechanism. |

The table's verdicts are advisory lens outputs per the honesty constraint above; the
convergence, not any single verdict, is the finding.

## Consolidated blocking gaps, ranked

Deduplicated across the four lenses and ranked by how many lenses hit the same wall and how
much else rests on it. Each gap names its evidence.

### Gap 1 — The cryptographic trust layer is built, witnessed, and inert; it covers none of the evidence that exists

Every mechanism of [design/GPG-TRUST-LAYER.md](MAINT-GPG-TRUST-LAYER.md) is implemented and
seen-red-witnessed (CAPABILITIES.md items 28–30), but only against throwaway test keys. As
of this writing (verified 2026-07-12, above): no maintainer key has ever been generated, no
`ratified/*` tag exists, no real chain head has ever been signed, and no existing world's
ledger carries `row_hash` — s26 entered the [birth chain](../GLOSSARY.md#birth-chain) after
runs 7, 10, and 11 were born, and [deltas](../GLOSSARY.md#delta-kernel-lineage-delta) are
never applied to settled worlds (the runs-are-linear ruling, CLAUDE.md). Consequence,
stated plainly: the properties the GPG layer exists to provide — non-repudiation, forgery
resistance against the apparatus itself, outside-verifiability
([GPG-TRUST-LAYER.md](MAINT-GPG-TRUST-LAYER.md) §1) — exist today for nothing real. "Append-only
or provably broken" is true of scratch fixtures only; for runs 3–11 the append-only
guarantee is a database trigger the same passwordless superuser of Gap 2 could drop
([s26's own header](../kernel/lineage/s26-row-hash-chain.sql) names this limit). All four
lenses ranked this at or near the top; the ICJ lens rated it critical because the corpus an
examiner would actually be handed is exactly the uncovered part.

### Gap 2 — The perimeter and the substrate: an open door in front, no floor underneath

Two halves are live-verified here, both dated 2026-07-12. **The door:** the Postgres role `bork` is a
superuser with no password, reachable over the network, TLS off — and the prepared fix
(PG-HBA-HARDENING.md (the maintainer-internal pg_hba hardening write-up, not part of this public release)) has sat unapplied; CAPABILITIES.md's "Not yet
enforced" section names pg_hba hardening as unscheduled. This credential bypasses every
control the harness has: triggers, stamps, grants, views. **The floor:** no backup,
replication, retention, or disaster-recovery story exists anywhere for the single Postgres
instance holding every world's ledger — three lenses searched independently
(BACKLOG.md, CAPABILITIES.md, design/, law/briefs/) and found no artifact; the only
"retention" language in the tree covers engine derivation records under
`engine/docs/`, which is what the conformance map's I11 row cites, not database
durability. (The "I" numbers used throughout this document — I1, I6, I8, I9, I11, I12 —
are the BRIEF's §2 cross-domain invariants, the numbered properties the conformance map's
rows assess; I11 is endurance and availability.) Every guarantee in the project ultimately rests on one disk nobody has
promised to copy.

### Gap 3 — No configuration index: the apparatus is deliberately unpinned, so nothing records which instrument version produced or reads which evidence

The "live verbs" model ([OPERATING-CARD.md](../ORCH-OPERATING-CARD.md), "What this is") means
hooks and operator verbs execute from the *current* autoharn checkout on every invocation
in every wired world — including settled evidence worlds. The scaffold's PROVENANCE header
records the birth command and the kernel SQL chain
([bootstrap/new-project.sh](../bootstrap/new-project.sh)) but not the autoharn commit hash;
so no artifact anywhere ties a historical DENY/ALLOW, a stamp, or an audit verdict to the
hook bytes that produced it, and re-querying run 7 today uses today's instrument code, not
run 7's. In DO-178C vocabulary this is the Software Configuration Index / tool
configuration index (the record of exactly which tool and process versions produced which
evidence) failing by design rather than by omission — a deliberate ergonomics
ruling whose auditability price had not previously been written down. The NRC lens flags
the same fact as an I8-shaped instrument-stability gap the conformance map has no row for.

### Gap 4 — Independence is invocation-distinctness inside one trust domain, and the record cannot show review depth

What s21 mechanizes is real and live-witnessed: a review claiming independence is refused
at write time unless a provably distinct (session, agent) invocation wrote it
([kernel/lineage](../kernel/lineage/), CAPABILITIES.md item 3). But every
[principal](../GLOSSARY.md#principal) is a Claude instance on one host, under one operator,
one vendor, one Postgres, with the [stamp](../GLOSSARY.md#stamp) secret on the same host it
attests — the project's own words: "a tripwire, not authentication" (CAPABILITIES.md
"Honest limits") and "everything the harness proves today, it proves inside one trust
domain" ([GPG-TRUST-LAYER.md](MAINT-GPG-TRUST-LAYER.md) §1). Nuclear-culture independence
(technical/managerial/financial — the BRIEF's I6 backing) is organizational separation this
deployment structurally cannot produce, only disclose. The sharpest current edge is the
run-11 retrospective's own finding: the record can witness that review *happened* and
*read* the files, but not that it *reasoned* — review's load-bearingness turns UNDECIDABLE
exactly when review finds nothing ([RETROSPECTIVE-RUN11.md](ORCH-RETROSPECTIVE-RUN11.md),
closing finding).

### Gap 5 — The verifier is unverified, and the contemporaneity verdict has one producer

Two instances of one shape: the harness holds the subject to a dual-derivation,
seen-red-proven bar it does not yet apply to itself. (a) The hooks and gates — the tools
whose refusals the whole record trusts — have no unit/regression test suite anywhere in the
tree; their verification evidence is the seen-red fixture corpus, which is real,
both-polarity integration proof but carries no coverage claim, and BACKLOG.md's "Run-11
first-shift forensics (2026-07-11)" entry documents a live instance of the failure mode
this invites: a doc gate that fail-opens silently on internal exception, indistinguishable
world-side from a clean pass. In the vocabulary of DO-330 (DO-178C's tool-qualification
supplement) the tool-qualification trigger (output trusted without independent
verification) is met and unaddressed for the entire hook/verb layer. (b) The contemporaneity audit ships one producer — the ASP derivation — with the
SQL-floor differential filed, not built (CAPABILITIES.md item 24, "second-producer status,
declared honestly"), and its thresholds are reasoned lower bounds from one or two
specimens ([engine/contemp_thresholds.lp](../engine/contemp_thresholds.lp)'s own
derivation comments), unlike every kernel verdict, which gets the AGREE discipline.

### The rest of the consolidated list, compressed

Ranked 6–10, each real, none top-five: **(6)** contemporaneity itself — I1 stands
self-downgraded to "VIOLATED in witnessed practice" in
[the conformance map](../law/briefs/BRIEF-CONFORMANCE-MAP.md), the audit cannot reach the
corpus predating [s23](../kernel/lineage/s23-per-invocation-stamp-token.sql) — the kernel
step that stamps each row with its invocation token; earlier worlds get a typed
NO_VERDICT refusal — and `event_declared_ts` is an unauthenticated
writer-supplied claim that fully launders a would-be BACKFILL_SUSPECT into LATE_DECLARED
([s24's own header](../kernel/lineage/s24-declared-event-time.sql) discloses this
plainly); **(7)** traceability's gap-detection half — s25 captures commissions but no view
detects a decomposition or work item that fails to cite one (the delta's own named limit,
CAPABILITIES.md item 26), so run-11's citation audit had to be done by hand; **(8)**
problem-report discipline regressed across the era boundary —
[gates/findings_gate.py](../gates/findings_gate.py) enforces a closed disposition
vocabulary against the retired predecessor schema, and the current kernel has no
CHECK-enforced disposition for `kind='finding'` rows (closures live in BACKLOG prose);
**(9)** the git substrate is unsigned (every commit) and was legitimately rewritten twice
(the 2026-07-07 privacy incidents, BACKLOG.md dated entries) — documented, defensible, and
still the first thing a hostile examiner opens with; **(10)** N=1 witnessing — the
project's own standing caveat (conformance map: "one run is a proof of mechanism, not a
distribution") — is honest and is also, to any of these institutions, an evidence-volume
gap only calendar and more runs can close.

## What is already sufficient — credit where the lenses agreed it lands

The plan below deliberately does not rebuild any of this. All four lenses independently
credited:

- **The append-only ledger with typed correction edges**, refused by trigger (not
  convention), with `supersedes`/`amends` exercised organically and both polarities banked
  (CAPABILITIES.md item 1; `seen-red/06-append-only-integrity/`).
- **Write-time attribution plus mechanized separation of duties**: the HMAC stamp injected
  by hook, and s21's pair-distinctness refusing inflated independence claims live — a
  genuinely independent reviewer catching a real defect the author's verification passed
  (CAPABILITIES.md items 2–3).
- **The seen-red discipline itself**: 40+ dated fixture directories, each a gate actually
  witnessed refusing, registered in a census the pre-commit chain enforces
  ([hooks/pre-commit](../hooks/pre-commit), [seen-red/](../seen-red/)).
- **Closed verdict vocabularies everywhere** — never a boolean, never silence, refusals
  typed distinctly from failures (`AGREE|DIVERGE_BY_DESIGN|DIVERGE_DEFECT|QUARANTINED`;
  `NO_VERDICT` vs `VACUOUSLY_CLEAN`; `NO-COMMITTED-KEY` vs `FORGED-OR-CORRUPT`) — the
  BRIEF's I9 actually practiced.
- **Dual independent derivation for kernel verdicts** (`./judge`'s SQL/ASP marriage with
  banked DerivationRecords — the per-solver-run provenance records pinning
  engine+version+config+hashes, retained under `engine/docs/ledger-marriage/derivations/`
  and described in CAPABILITIES.md item 12 — I8 honestly scoped to the engine layer).
- **The self-indictment culture**: the I1 downgrade written into the map *before* the fix
  existed; the "half fixed" correction after the maintainer caught an overclaim; two real
  defects (a hash collision, a verdict overload) found by out-of-frame adversarial audits
  and fixed before "done" was reported (BACKLOG.md "GPG trust layer — all three rungs
  built and witnessed"). Several lenses noted their findings were discoverable *because*
  the project discloses against itself — a property none of these institutions can compel
  and all of them prize.

## Features missing from the map's own frame

The commission's second question. These are not unfilled rows in
[BRIEF-CONFORMANCE-MAP.md](../law/briefs/BRIEF-CONFORMANCE-MAP.md) — they are questions
neither the map nor its source BRIEF ever poses, because the BRIEF's frame is the
*record's internal audit properties* (who wrote, who reviewed, what was retained) and
these live outside that frame. Grouped; the lens that surfaced each is named so the
reasoning can be traced.

**The substrate and the perimeter sit outside the frame (NRC, NIST, ICJ).** No invariant asks what happens when
the disk holding the ledger dies (I11's row is satisfied by derivation-artifact retention
while the database itself has no survival story), who else can reach the host and the
superuser role, whether the platform is patched, or whether anyone would notice unexpected
use of the one credential that bypasses everything. The BRIEF's source domains assume a
secured facility; this deployment has to supply that assumption itself, and the map has no
row where its absence would show.

**The frame never treats the apparatus as its own subject (NRC, FAA).** The map applies
I6 (independence) to subject rows, never to the authoring of kernel deltas — no row asks
who verifies changes to the governance mechanism itself, or whether the
class-ratification path's adversarial audit is stamp-distinct by the kernel's own
standard (the FAA lens marked that UNDECIDABLE from the artifacts). "Class-ratified" is
the standing [CLAUDE.md](../CLAUDE.md) rule that a strictly fail-safe kernel delta — one
that only ADDS refusals, vocabulary, or derived views, scratch-witnessed both polarities
with the differential in AGREE — may enter the birth chain without a per-delta maintainer
question; "class-ratifiable" below marks plan items that qualify. I8 (tool provenance) stops at the solver layer — no row
asks about psql, Postgres, Python, Claude Code's hook contract, or the model itself; a
model-version change is not treated as a tool-qualification event anywhere, though the
model is the least deterministic tool in the chain. And no row asks whether the audit
*instruments* are version-pinned to the evidence they read (Gap 3): instrument stability
is simply not a concept the frame has.

**The frame never examines the institution around the record (NIST, ICJ, FAA).** No row asks about custodianship —
the administrator of the system of record and the party the record holds accountable are
the same person, the collapse the financial cluster's designated-third-party concept
exists to prevent (the BRIEF cites 17a-4 for retention but never imports the custody
question). Nothing addresses key-person continuity (what happens to the ledger and any
future signing key if the one human is unavailable — the succession rule, the
[CLAUDE.md](../CLAUDE.md) ORCHESTRATION provision for who may author constitutional
specs when Fable is unavailable, covers spec authorship only), incident response as a process (the two privacy incidents were handled
well but ad hoc), data classification of ledger content (what must never be *written*
into an append-only record — the ephemera incidents show the hazard), or spoliation
posture for the git substrate the chain, keys, and attestations live in (rewritten twice,
documented in prose only). Key custody is treated as binary signed/unsigned; the real
question is a gradient — where the key lives relative to what it attests.

**Proportionality and product depth go unasked (FAA).** The BRIEF assumes the subject is
life-critical; the map inherits that and applies uniform rigor whether the run's subject
is an interlocking or a terminal-colors webapp. No lever exists to grade assurance effort
to consequence (the Design-Assurance-Level / Safety-Integrity-Level idea: rigor scaled to
how much a failure costs), so over-application is as invisible as under-application. And the harness governs the *decision trail*, not the *product's
verification depth* — no row even declares structural coverage of the subject's own code
as an exclusion; it is simply absent. Related: the map's "built-unexercised" prose has no
mechanical counterpart — nothing inventories, across worlds, which mechanisms are
currently OFF in each `apparatus.json` against what the maintainer intended (the
deactivated-code question).

**Cross-world common cause is never analyzed (NRC).** "One world per run" is stated as isolation policy;
no row asks whether a subject role in one schema can reach a sibling's, or what failure
modes the worlds share through their one host, one db, one hook codebase — the BRIEF's
own F15 (common-cause analysis) applied to the apparatus's multi-tenancy, which the map
never does.

## The proceed-plan

The items below are ranked and costed (S = hours, M = days, L = weeks or structural).
Ordering principle:
arm what is already built before building anything new; close the perimeter before
refining the record; every item respects the standing rulings (restated at the end).
Maintainer-act items are flagged — they are decisions or ceremonies only he can perform.

**Tier 1 arms the existing machinery (mostly S, mostly maintainer acts).**

1. **Generate the real maintainer keypair** (hardware token per
   [GPG-TRUST-LAYER-FAQ.md](USER-GPG-TRUST-LAYER-FAQ.md)), commit `law/keys/maintainer.asc`,
   sign the first `ratified/*` tag, run `./attest-tags` for real. S; maintainer act; turns
   Gap 1's Rung 1 live with zero new code.
2. **Apply the prepared pg_hba hardening** (PG-HBA-HARDENING.md (the maintainer-internal pg_hba hardening write-up, not part of this public release):
   password + scram host lines). S; maintainer act; closes Gap 2's door.
3. **Scaffold the next world on the current chain (s26 is already in it) and sign a real
   chain head at close.** S–M; first genuine "append-only or provably broken" world.
4. **Record the autoharn commit hash in every future world's PROVENANCE header and
   `deployment.json`** at scaffold time. S; additive; gives Gap 3 a birth-time anchor for
   all future worlds (the live-verbs ruling itself is untouched — this prices it, not
   reverses it).
5. **`apparatus.json` unknown-key sweep** (a typo'd mechanism name currently disables a
   mechanism silently — BACKLOG.md "Configuration-surface survey" gap 1). S; a pure
   added refusal, class-ratifiable.

**Tier 2 closes the named halves (M).**

6. **A scripted, witnessed backup verb for the toy db** (pg_dump or WAL archive to
   storage off the host) plus one exercised restore drill on a scratch copy. M; closes
   Gap 2's floor; the self-application ruling makes this a verb, not a runbook.
7. **The SQL-floor second producer for `./audit`**, giving the contemporaneity verdict
   the same AGREE discipline every kernel verdict has (already filed; CAPABILITIES.md
   item 24). M.
8. **The commission-traceability view** s25's own header names as the natural follow-on:
   every `work_opened` (and decomposition row) traceable to a commission via refs,
   orphans visible. S–M; additive view, class-ratifiable; closes Gap 7's detection half.
9. **External as-of anchors for the settled corpus**: export each settled world's rows
   read-only, hash the export, and (once item 1 exists) GPG-sign the digest — labeled
   explicitly "as-of attestation", never "chain protection", touching no old schema. M;
   the only linearity-respecting remedy for Gap 1's uncovered corpus.
10. **Unit/regression tests for the two highest-authority hooks**
    (`stamp_intercept.py`, `pretooluse_change_gate.py`), then outward — closing the
    named fail-open class run-11's forensics found. S per hook to start; Gap 5(a)'s
    floor.
11. **A finding-disposition vocabulary in the current kernel** (the s22
    witness-required-CHECK pattern ported to `kind='finding'`), wired into
    `distance-to-clean`. M; kernel delta, likely class-ratifiable (adds a refusal);
    closes Gap 8.
12. **Sign commits going forward** once the key exists, and add a git-native marker at
    the two documented history rewrites. S; Gap 9's forward half.

**Tier 3 is structural — decisions rather than code (L; every item routes to the maintainer).**

13. **The trust-domain decision**: either engineer a second channel outside the single
    domain (a second human principal with their own key — the multi-human extension
    [GPG-TRUST-LAYER.md](MAINT-GPG-TRUST-LAYER.md) §5 already designs; or an
    externally-hosted attestation anchor), or ratify a written acceptance of the
    single-domain limit with the compensating controls named. Gap 4 cannot be closed by
    code alone; the decision itself is the deliverable.
14. **Independence for the apparatus's own change process**: a structurally separate
    review channel for kernel-lineage deltas, including class-ratified ones — applying
    the existing ceremony to the verifier itself. L; law-adjacent, full ceremony.
15. **A tool-qualification package for the hook/verb layer** (operational requirements,
    a verification-cases document built from the existing seen-red corpus, the
    configuration-index anchor from item 4). L; Gap 5(a) at full depth.
16. **Corpus accretion**: more real runs, then re-measure the contemporaneity thresholds
    and the observer instruments' precision against a distribution instead of specimens.
    Calendar-bound by nature; the code already names its re-measurement triggers.

**Out of scope on principle: the plan deliberately contains none of the following.** No
committing of session [ephemera](../GLOSSARY.md#ephemera) or transcripts (the privacy
ruling stands; the evidentiary lens's completeness objection — the ledger is a summary
the writer chose to write, deliberation is invisible by design — is answered by policy
regularity and the stated action-stream principle, not by disclosure). No LLM verdict in any blocking or verdict path — the
review-depth gap (Gap 4) in particular must not be "solved" by an LLM grading review
quality into a gate; any depth instrument stays on the action stream (e.g. structured
review-coverage fields, read-attribution) and advisory. No token/cost accounting in the
audit trail (the action-stream principle: `~/.claude` internals are diagnostics,
permanently). No patching, refreshing, or delta-ing settled worlds — every remedy for the
existing corpus is external-anchor-shaped (item 9), never retroactive. And no weakening
of any refusal for agent comfort: auditability outranks ergonomics (maintainer priority
ruling, 2026-07-11).

## Related

- [law/briefs/BRIEF-CONFORMANCE-MAP.md](../law/briefs/BRIEF-CONFORMANCE-MAP.md) — the
  standing self-assessment whose frame this document audits from outside; its rows and
  this document's gaps are complementary, not competing.
- [law/briefs/safety-critical-logging/BRIEF.md](../law/briefs/safety-critical-logging/BRIEF.md)
  — the aspiration layer; its §2 invariants are the vocabulary the lenses tested against.
- [design/GPG-TRUST-LAYER.md](MAINT-GPG-TRUST-LAYER.md) and
  [design/GPG-TRUST-LAYER-FAQ.md](USER-GPG-TRUST-LAYER-FAQ.md) — the built-but-unarmed layer
  Tier 1 arms.
- design/PG-HBA-HARDENING.md (the maintainer-internal pg_hba hardening write-up, not part of this public release) — the prepared perimeter fix.
- [CAPABILITIES.md](../ORCH-CAPABILITIES.md) — the witnessed-capability inventory every
  "already sufficient" credit above cites.
- [law/adr/0017-the-zero-context-reader.md](../law/adr/0017-the-zero-context-reader.md)
  — the legibility law this document is written under; its attestation record lives in
  [attestations/doc-legibility-attestations.jsonl](../attestations/doc-legibility-attestations.jsonl).
