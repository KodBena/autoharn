# Engine assurance arguments SEED — the BRIEF:F10 conservative-abstraction argument and the BRIEF:F12 assurance-case structure

**Status:** SEED, for maintainer review. No code changed; two hazards found in passing are
FILED (findings ledger, db/harness/005) and flagged loudly in §1.4 — not fixed here,
because the exporter is a two-producer evidence surface and a silent edit to it mid-chain
is exactly what the change-discipline forbids.

**Commission:** the seed's structural mandate 7 (`consults/engine-design-SEED.md`: "The
unowned BRIEF items: F10 … F12 … Each gets an owner or a declared exclusion at elevation —
silence is the one forbidden state") and inc-0's open-questions register rows OQ3/OQ4
(`consults/engine-increment-0-unification.md` §7, owner class: Fable). The critic's
verbatim framing binds this document (`consults/engine-panel/critic-completeness.md` §4):
"The engine substitutes mechanical derivation for human review of the record" (F10), and
"'proved in clingo' is a talisman without the argument" (F12).

**MODEL-SERVED (self-report):** claude-fable-5, per this session's own system context
("You are powered by the model named Fable 5. The exact model ID is claude-fable-5").
Standing caveat, carried verbatim in spirit from every panel document: there is no
introspective channel that could detect a silent mid-run substitution; no degradation
event was observed this invocation.

**Record basis — read in full this invocation:** the safety-critical-logging BRIEF
(`claude_harness/experiments/fact-mining/docs/safety-critical-logging-standards/BRIEF.md`);
`consults/engine-design-SEED.md`; `consults/engine-panel/critic-completeness.md`;
`consults/engine-increment-0-unification.md`; `LEDGER-LOGIC-MARRIAGE.md` (body +
Appendix A); ADR-0000, ADR-0012, ADR-0013, ADR-0014 in full; and — because F10(b) demands
the abstraction be named from the artifact, not the design doc — the as-built code:
`experiments/fact-mining/ledger_edb.py` (whole file), `ledger_tnow.lp` (whole file),
`ledger_floor.py` (header + CTE structure), `instruments/close_manifest.py` (manifest
line registry), the s13 kernel write-boundary triggers
(`harness/e13-build/s13-schema.sql`, the `validate_amends` block), and the semantics
design's family table (`consults/engine-panel/design-semantics.md` §2). Where this
document asserts a code fact it cites the file; every such fact was read at authoring
time, not cited from memory (the evaluation-refutation flaw-1 lesson: the one file cited
from memory is where an otherwise-faithful author is reliably wrong).

**Law keys are namespaced throughout** per inc-0 D15: `BRIEF:F10` = the log-register row,
`FIND:F44` = the project finding, `INV:I7` = the BRIEF invariant, `RULING:42` = the
acts.ruling row, `ADR:0000` = the chocofarm law.

---

## 1. THE F10 ARGUMENT — why ids-not-text derivation may substitute for human review, and exactly where it may not

### 1.0 What is being claimed, in one plain paragraph

The deductive engine reads an exported fact base (the EDB) that deliberately contains
**no prose** — row ids, timestamps, kind/status atoms, and typed edges, never the
statement text, the rationale, or the quoted clause. Over that skeleton it derives
judgments (in-force, unsound-derivation, question-open, clause-defeat, stale-debt) that
would otherwise require a human to re-read the whole record. BRIEF:F10 says: when a
formal method substitutes for another verification means, you must name the gap between
the model and the real thing, and argue that the gap **errs toward false alarms, never
toward false green** — and where it does not, name the compensating control or file the
hazard. This section is that argument, built from the as-built exporter, not the design
doc — and the two places where the as-built exporter and its own documentation disagree
are themselves findings (§1.4).

### 1.1 The abstraction, named precisely (F10(b) input)

**What the EDB actually carries** (`ledger_edb.py::export`, read at source):

| Fact | Emitted from | Precision notes |
|---|---|---|
| `entry(Id, Ts, Kind, Concern, Status, Confidence)` | every ledger row, `ORDER BY id` | `Ts` truncated to epoch **seconds**; `Concern/Status/Confidence` NULL-coalesced to `''` → atom `none`; a target **lacking the column entirely** also emits `none` (same spelling) |
| `supersedes(A,B)`, `enacts(E,D)` | always | `enacts` array-unnested or scalar, auto-detected |
| `amends(A,T)`, `answers(A,Q)` | column-gated (declared absent on pre-e13 lineages) | edge only — see the omission list |
| capability manifest header | per target | DEFERRED vs EXCLUDED distinguished; `require()` refuses any un-emitted family loudly (the F49 fix, `Capability.produced` vs `.capable`) |

**What the EDB omits.** Two layers, and the distinction carries the whole argument:

**Layer 1 — omissions the capability manifest CAN see (declared, refusal-guarded).**
The kernel-shape families (`regards`, `review_verdict`, `review_independence`, `obliged`,
`acts_for`, `agent_class`) are declared DEFERRED (capable, no consumer this increment) or
EXCLUDED (schema cannot carry them), and `EdbExport.require()` raises `CapabilityError`
on any request for an un-emitted family. Omission here is **conservative by mechanism**:
it fails toward loud refusal, never toward a silent empty relation read as "none exist".
This is the one part of the abstraction that needs no direction argument — the mechanism
*is* the direction.

**Layer 2 — omissions the manifest CANNOT see** (they are below its granularity, outside
its closed vocabulary, or properties of the export act itself). Enumerated exhaustively
against the export code and the kernel schema:

1. **Statement text** (`ledger.statement`) — never crosses.
2. **Rationale prose** (`ledger.rationale`) — never crosses.
3. **Evidence pointers** (`ledger.evidence`) — never cross.
4. **`amends_scope` content — and, as built, even its length.** The marriage §3
   signature promises `amends_scope_len(A, N)`; `ledger_edb.py`'s own docstring claims
   "`amends_scope` crosses as its length only"; the export code emits **neither** — only
   the bare `amends(A,T)` edge. Design, docstring, and code are three-way divergent
   (finding filed, §1.4).
5. **Actor / attribution** — the marriage §3 signature promises `actor(Id, PrincipalId)`;
   the as-built exporter emits no actor fact **and `actor` is not in the capability
   vocabulary at all**, so its absence is not even a declared exclusion. `require("actor")`
   does refuse ("not a known fact family") — loud, but mislabeled: it *is* a known family
   per the design signature (finding filed, §1.4).
6. **Sub-second time** — `ts` crosses as epoch seconds; sub-second ordering information
   is destroyed (deliberately irrelevant: no rule orders on ts, id is the order —
   `ledger_tnow.lp` header, design §3 rule 2).
7. **NULL-vs-`none` and absent-column-vs-NULL collapse inside `entry/6`** — three
   distinct substrate states (column absent; column present, value NULL; column present,
   value literally spelling a none-like atom) map to the one atom `none`. The capability
   manifest is per-*family*; `entry/6`'s optional arguments smuggle three
   sub-capabilities through it undeclared.
8. **Everything outside the `ledger` table** — the acts stream, the s17+ stamp
   relations, `kernel.principal`, the gate journal. Families never named in the closed
   vocabulary are invisible to the manifest's self-disclosure: the manifest can only
   declare absences it has names for (INV:I12 has a horizon, and the horizon is the
   vocabulary).
9. **Snapshot atomicity** — the export issues **one psql invocation per fact family**
   (entry, then supersedes, then enacts, then amends, then answers — five separate
   read transactions). The EDB therefore corresponds to a *vector of slightly different
   implicit frontiers*, one per family, and to no single `Frontier` at all whenever any
   writer is active during export. The SQL floor, by contrast, is a single
   `WITH RECURSIVE` statement — snapshot-consistent by Postgres MVCC. The two producers
   do not share this defect, which matters below.

### 1.2 Direction analysis — per omission, per judgment (F10(c) input)

The claim set the direction is argued against is the **registered judgment set as
built** — the `#show` list of `ledger_tnow.lp` (`in_force`, `head`,
`unsound_derivation`, `launder`, `alias_surface`, `stale_enactment_row`,
`question_open/answered`, `clause_defeat{,_moot,_withdrawn}`, `condition2_individuation`)
plus its SQL-floor twin. Direction vocabulary: **conservative** = the omission can only
produce a false alarm or a loud refusal, both visible; **non-conservative** = the
omission can produce a false green (a defect the derivation is read as excluding, yet
does not); **exact** = the omission is outside the judgment's quantification, so the
projection is lossless *for that judgment*.

| # | Omission | Direction | Argument | Compensating control (existing = verified at source; else honestly absent) |
|---|---|---|---|---|
| 1–3 | statement / rationale / evidence text | **exact, by claim-scope construction** — with a named informal-reading residual | No registered judgment quantifies over text. Reference *truth* (does cited content match citing intent), MECE-of-meaning, rationale sufficiency are Family H by law (marriage §4 last row: "no engine claims it"). The abstraction errs non-conservatively **only if a consumer reads a structural verdict as a content verdict** — which is a claim-scope violation, not a derivation error. | The F12 disclaim list (§2.6) exists to make that misreading impossible to commit innocently. Content-adjacent checks that DO need text run where text lives: the write-boundary triggers (below) and the SQL-side instruments (`cite_check.py` reads the statement log; review queue routes Family H to a human). |
| 4a | `amends_scope` content | **conservative for edge validity; non-conservative for the informal reading of IN-FORCE** | The engine cannot check the quotation — but it never needs to: the kernel's `validate_amends` trigger (s13-schema.sql, verified: both-or-neither, ≥10 chars, `position(NEW.amends_scope IN t_statement/t_rationale) > 0`, earlier-target) proves at **write time** that every `amends` edge in the record carries a verbatim quotation of the target's own text. The engine consumes a fact the substrate has already verified — the trigger is the compensating control, and it is real and armed. The residual is sharper: `in_force(T)` remains true under clause-defeat (row-granular law, consult 19 §1.3 surviving clause, FIND:F44), and **the engine is structurally blind to whether the defeated clause is the load-bearing one**. A consumer reading IN-FORCE as "content trustworthy" gets a false green. | Existing: the `clause_defeat(A,T)` flag itself is derived and routed (the defeat is never silent — the *row* is flagged even though its severity is unknowable mechanically); the write-time quotation validity above. Designed, NOT built: the FDE `both`-rendering (marriage §9.5, increment 5 — unbuilt as of this authoring) and the D9 `scope_token` opaque subject (inc-0). Honest residual: clause **severity** is Family H forever — no mechanical layer will carry it; the disclaim list carries it instead. |
| 4b | `amends_scope_len` promised, not emitted | **conservative in effect, dishonest in documentation** | No current rule consumes the length, so nothing derives wrongly. But the module docstring claims the length crosses — a reader auditing the abstraction from the docstring would name a *smaller* gap than exists. A lying doc about an abstraction gap is an F10-register defect in its own right (the gap statement is itself evidence). | None. **Filed** (§1.4, finding 2). Fix is one line of code or one line of docstring; which one is a design decision (does any planned rule need the length? condition-2 accumulation weighting might) — owner: stand-in build, under this SEED. |
| 5 | actor / attribution | **conservative by refusal — with an undeclared-absence defect** | No engine judgment claims actor properties today (verified: `ledger_tnow.lp` contains no actor literal). Family E judgments that need attribution (SoD, independence, F53-class) run **in the kernel, SQL-side, with full access** — the e17 stamp gates are write-time kernel triggers, not EDB consumers. So nothing false-greens. The defect is I12-shaped: the absence is not *declared* (actor is outside the closed family vocabulary), so the manifest under-discloses the gap, and a future Family-E encoding could be authored against the EDB in good faith and ground empty — clingo's unmatched-body-predicate path, the exact class INC 3's grounding witnesses are commissioned to promote to RED, **which are not built yet**. | Existing: `require()` refuses; the kernel gates carry Family E. Owed: add the actor family to the vocabulary as a declared DEFERRED capability (stand-in, one-line class of change); INC 3 grounding witnesses close the silent-empty class wholesale. **Filed** (§1.4, finding 2 covers the signature divergence). |
| 6 | sub-second ts | **conservative / exact** | No ordering keys on ts (id is the order — the same-second-neighbour fixture is the standing proof this matters). The only ts consumers are display and INV:I7 bounds (`ledger_assumes.lp` expiry): 1 s truncation can flip an expiry verdict only within a 1 s window of the bound, and the expiry family's verdict is a *flag*, warning-polarity (D14) — a 1 s-early EXPIRED is a false alarm, visible; a 1 s-late one is caught at the next derivation. Bounded, declared, both-directions-visible. | The Frontier type (inc-0 D6) pins the evaluation clock in the DerivationRecord, so replay reproduces the same verdict — the imprecision is stable, not drifting. |
| 7 | NULL / `none` / absent-column collapse | **latent non-conservative — currently unexercised** | Today no rule reads `Concern/Status/Confidence` (verified: `ledger_tnow.lp` matches on Kind only, always NOT NULL). The day a rule quantifies over status ("every decision row carries a status", "no in-force row is `provisional`"), a target *without the column* emits `none` everywhere and the rule goes **vacuously green** — the F49 shape reproduced one level below the manifest's granularity, on the most-capable-looking path (`entry/6` is ALWAYS "produced"). | None mechanical today. Foreclosure is typed (ADR:0000 Rule 2a): per-argument capability rows, or a distinct `absent` atom so column-absent ≠ NULL ≠ `none`-valued — unrepresentable confusion instead of reviewed-for confusion. **Registered as an admission precondition**: no rule that binds `Concern/Status/Confidence` may be admitted to the registry until the per-argument declaration lands (this sentence is the interim control — it converts the silent class into a checkable registry rule). Owner: stand-in, at INC 2 (the enum/manifest generator is the right home). |
| 8 | non-ledger relations | **conservative by claim scope + I12 horizon caveat** | Judgments over streams the EDB does not carry are not derivable, and the registry's `edb_availability`/EXCLUDED machinery (inc-0 §1.1) exists to say so per judgment. The caveat is honest: the manifest self-discloses only within its named vocabulary. The BRIEF's I12 wants the *record* to state its own boundaries; the boundary statement for whole absent streams lives one level up — the conformance map and the registry, not the per-export header. | The registry (INC 1) with two-way parity: a judgment with no implementable substrate is a REQUIRED-ABSENT/EXCLUDED row, never silence. |
| 9 | snapshot non-atomicity | **NON-CONSERVATIVE, uncompensated at turn-time — the sharpest gap this argument found** | Under any writer concurrent with export, the five per-family reads see five different record states. Append-only means each later-read family is a superset relative to the entry snapshot; tracing the rule bodies: extra `supersedes` → over-defeat → false alarms (conservative); but `answered(Q) :- answers(A,Q), not superseded(A)` (`ledger_tnow.lp` — deliberately entry-unguarded on A) can consume an `answers` edge from a row **outside the entry snapshot**, flipping `question_open(Q)` to answered at a frontier where it was open — a **false green** on the open-questions readout; and `in_force(E)` under-approximation silently *removes* `stale_enactment_row(E,D)` flags — a **missed flag**. The EDB hash pins the torn state faithfully, so replay reproduces the tear: replayability and frontier-soundness are different properties, and only the first holds. | Existing, partial and accidental: at close, the differential compares the ASP producer against the **single-statement** SQL floor (`ledger_floor.py` — one `WITH RECURSIVE`, snapshot-consistent); a torn EDB diverges from the atomic floor and the run goes red (A.5 closed vocabulary). But that net exists only where the differential runs, and the T1 turn-time hook (OQ15) would consume the EDB **without** it. Existing, assumptive: the single-writer/quiescent-export operating assumption — already flagged as unowned by the critic (§3 "frontier = max id at export … silently assume a single writer", OQ14). This SEED sharpens it from a general concurrency worry to a **named, one-module, cheaply-foreclosable defect**: export all families in one read transaction (or `WHERE id <= pinned-max` per family against one pinned max). **Filed** (§1.4, finding 1). Owner: stand-in (the fix is mechanical); the Frontier retrofit (INC 2) should treat it as a precondition — a `Frontier` vector stamped on a torn export is a false provenance claim. |

**The structural summary of (c).** The abstraction is **exact** for what the registered
judgments actually quantify over (ids, edges, kinds — copied 1:1, id-ordered,
hash-pinned); **conservative by mechanism** for every omission the capability manifest
can name (refusal, never silence); and **non-conservative in exactly three named places**:
the torn-snapshot export (mechanical, foreclosable, filed), the latent
`entry/6`-argument vacuous-green (latent, admission-gated, filed with its foreclosure
type), and the informal reading of IN-FORCE over clause-defeated content (permanent
J-boundary residual, carried by the disclaim list and the routed `clause_defeat` flag,
retired case-by-case only by DTO fragments). No other direction-of-error was found, and
the enumeration above is the quantification universe of that claim (ADR:0000 closure
discipline): axes = {text columns, edge annotations, attribution, time precision, null
representation, vocabulary horizon, export atomicity}; targets = the emitted fact
families of `ledger_edb.py` as built.

### 1.3 The F10 entry, in the BRIEF's required (a)–(e) shape

Ready to bank as the engine's F10 row (BRIEF §3.2: "An entry missing any of (a)–(e) is
incomplete, not merely thin"). Each part states its evidence pointer.

**(a) Soundness pedigree of the tool.**
- Calculus: clingo answer-set semantics over a program that is **stratified on the
  as-built rule set** (append-only + earlier-target validation make every defeater edge
  strictly backward in id, so the closure has one unique model where stable-model and
  well-founded semantics coincide — semantics design §3; the acyclicity that licenses
  this is itself checkable and is commissioned as a Family A judgment, RED before any
  nonmonotone rule fires). We never depend on answer-set multiplicity.
- Runner honesty: `clingo_run.py` raises on any non-solved result (`_SOLVED_RESULTS`
  incl. `OPTIMUM FOUND`; the durable grounding-error fix, regression-tested) — a broken
  program cannot bank an empty model as a derivation (the A.8 hazard, closed).
- Second engine: z3 (SMT/FDE lanes) under the same seam, differential on shared rules.
- **Qualification honesty (I8): neither clingo nor z3 is DO-330/TCL-qualified, and no
  qualification claim is made.** The trust basis is instead: (i) per-run DerivationRecords
  {engine+version, config, EDB/program/output hashes; a verdict without both records is
  NO RESULT} (marriage A.4); (ii) two genuinely code-path-independent producers — a
  Postgres `WITH RECURSIVE` floor and clingo — required to agree **bit-identically** on
  the banked record (A.5); (iii) golden fixtures that are adjudicated real defects, each
  with a mutation that flips its verdict (marriage §5, ADR-0011 seen-red discipline).
  This is qualification-by-differential-and-fixture, and its ceiling is stated in (e).

**(b) The abstraction gap.** §1.1, layers 1 and 2, items 1–9 — enumerated from the
as-built exporter, including the two places the code and its documentation diverge.

**(c) The conservativeness argument.** §1.2, per omission, with direction and control
per row; structural summary above. Explicitly NOT claimed: that the abstraction is
conservative *simpliciter*. It is conservative-by-mechanism at the manifest layer, exact
on the projected columns, and non-conservative in three named, individually-dispositioned
places.

**(d) Coverage equivalence — what the derivation closes, and what it does not.**
The proof-bearing surface closes exactly: the Family C T_now closure (in-force, head,
answered/open) and Family D consumption soundness (unsound_derivation, launder-as-
negative-control, alias_surface, stale_enactment_row, clause-defeat dispositions,
condition-2) **over the emitted fact families, at the exported frontier, on the
registered targets** — the `#show` set, nothing more. It does NOT close (each row here
is a declared non-claim, not an oversight): reference truth / content fidelity /
rationale sufficiency (Family H, review-owned); clause-defeat severity (J-residue,
above); Family E attribution judgments over the EDB (kernel-side controls own them);
Family B/F cross-stream judgments (close-time-bound by D13 until acts_live is ratified);
anything on streams outside the vocabulary (item 8); conduct outside the perimeter
(FIND:F38) and J-triggered omissions (the BRIEF's own M/J scoping, §4). Mapping to the
BRIEF register: this entry supports the engine's contribution to G6-class verification
records and the I9 discharge-status honesty of its own derivations; it does not discharge
G7 (see (e)), G13, F14, or any J-marked row.

**(e) Named independent acceptance — OPEN, honestly.** The differential's second
producer is **not** G7 independence: both producers, the fixtures, and this argument
share one author-mind (the Tier-1a birth-independence caveat, seed survivor list; the
panel's common-mode disclosure applies to this document identically). Independent
acceptance therefore requires, and this entry is INCOMPLETE until it has: (i) the
maintainer's ratification act on this SEED (an actor-attributed acts.ruling row, per the
standing anchor idiom), and (ii) the invited **non-Fable review** of the engine seed
family (POST-FABLE brief: "a non-Fable review of the engine seed has real value … as a
committed consult"), which should take §1.2's table as its attack surface — every
"conservative" cell is a claim to refute. Until both exist, the F10 row's honest status
is DRAFTED-UNACCEPTED, and any conformance sheet that lists it says so.

### 1.4 Hazards met in passing — flagged loudly, filed, not fixed here

Per the engineering-responsibility clause (the plank with the nail): both filed via
`tools/file_finding.py` at authoring time (general findings ledger ids **46** and **47**,
class `hazard`, frame `out-of-frame`), evidence-ref'd to this file and the source lines;
OPEN until an actor-attributed disposition.

1. **[finding 46] `ledger_edb.py` export is not snapshot-atomic** (one psql call per fact family; the
   EDB can correspond to no single frontier under a concurrent writer; false-green
   direction proven possible via the entry-unguarded `answered/1` rule and the
   `in_force`-guarded `stale_enactment_row`). Sharpens critic §3 / OQ14 to a named
   module and a mechanical fix (single read transaction or pinned-max-id reads). Must
   land before the INC 2 Frontier retrofit stamps Frontier vectors on exports, and is a
   hard precondition of any T1 hook consuming the EDB without the close-time floor
   differential behind it.
2. **[finding 47] Design/docstring/code three-way divergence on the EDB signature**: marriage §3
   promises `actor/2` and `amends_scope_len/2`; the exporter's docstring claims the
   length crosses; the code emits neither, and `actor` is absent from the capability
   vocabulary so its exclusion is undeclared (I12 under-disclosure inside the module
   whose charter is loud declaration). Disposition needs one design decision (emit the
   length? declare actor DEFERRED?) and is otherwise mechanical.

---

## 2. THE F12 ARGUMENT STRUCTURE — from "these manifest lines are green" to "the record is honest"

### 2.0 What this section is

The BRIEF (§1.8, GSN v3 / 15026-2): the assurance case is "an explicit argument
structure, not prose … the argument connecting a proof to the claim — not 'proved in
Coq/PVS/Z3' as a talisman." The engine's own panel produced evidence generators (close
lines, differentials, discharge tables) and no argument connecting them to any claim
(critic §4). This section is that argument's structure: goal-structured, GSN-flavored,
plain-text. Node vocabulary: **G** goal (a claim), **S** strategy (the inference rule
decomposing it — itself auditable), **Sn** solution (a retrievable evidence pointer),
**A** assumption (first-class, with truth-status and invalidating condition, so a later
falsification propagates to every goal it undermines), **J** justification, **C**
context, **U** undeveloped (open, shown deliberately). A wall of green with no argument
is exactly the dressed-up-QED (INV:I9) at system scale; equally, this argument with no
green lines is prose. The two are useless apart; the manifest supplies the leaves, this
supplies the tree.

Plain-language reading of the whole case in three sentences: *The record is honest* is
argued as *every kind of dishonesty we have named and mechanized is absent or flagged,
every check that was supposed to run provably ran, and everything we cannot check is
named out loud rather than silently included. The argument's strength is exactly the
strength of its assumptions (A1–A9 below), each of which says what would break it. What
the green does NOT mean is listed with the same prominence as what it does (§2.6).

### 2.1 The top of the tree

```
G0  "At the close of session S, evaluated at Frontier F, the ledgered record is an
     HONEST record of the subject's epistemic acts — complete over the machine-
     observable trigger set, uncorrupted, currently-valid where it claims validity,
     and with every mechanically-detectable ledger-vs-acts divergence surfaced —
     WITHIN the declared perimeter (C1) and threat model (C2)."

C1  Perimeter: what the write boundary captures (kind vocabulary, typed edges, gate
    coverage). Conduct outside it (FIND:F38) is out of frame BY DECLARATION.
C2  Threat model (standing scope ruling): the apparatus distrusts the LEDGER-VS-ACTS
    relation (epistemic honesty), not the subject as a sandbox adversary; passive
    primes are fixed, active-evasion residuals are pre-registered assumptions.
C3  Substrate: the target named by the ledger_target SSOT resolution, declared on the
    face of the close (the fc18 foreclosure: an instrument pinned to its birth
    instance passes silently everywhere else).
C4  "Honest" is a STRUCTURAL predicate over the record — see the disclaim list (§2.6)
    for the readings it does not carry.

J0  Why a decomposition by judgment family is sound: the family taxonomy (A–H) was
    derived by triangulating the BRIEF register (scope), the F-series (laws), and the
    e-series (specimens) — semantics design §2 — and the registry (inc-0 §1) makes it
    CLOSED: every registered judgment belongs to exactly one family, and the S2
    DischargeStatus map is TOTAL over the registry, so "a family's line is green"
    quantifies over a known, generated set, not an ad-hoc list.

S0  Argue G0 by (i) sub-claims G-A … G-H, one per judgment family, each supported by
    named manifest lines; PLUS (ii) the totality meta-claim G-T; PLUS (iii) the
    explicit assumption register A1–A9 and the disclaim list D. The inference is:
    G0 holds to the extent that {G-A…G-H} hold, G-T proves the set ran whole, and
    the As hold — and NOT otherwise. S0 is itself an auditable step: its soundness
    is J0's closure property, and an unregistered judgment or unmapped verdict is a
    parity failure that invalidates S0's quantifier, turning the whole case red.
```

**G-T, stated before the families because everything leans on it:**

```
G-T "Every mandatory line ran, on the declared substrate, and produced a status —
     non-run is unrepresentable as green."
Sn  close_manifest.py: the MANDATORY set runs under {OK | QUARANTINED(reason)}
    accounting, exits non-zero on any quarantine, declares db + journal window +
    repo span (verified at source: instruments/close_manifest.py header + MANDATORY
    list). The F49 negative control (delete a rule file → NOT-RUN → RED) and the
    meta-toolchain negative controls (never-invoked close, empty-register load,
    deleted-spec — inc-0 D2/INC 2) are its seen-red evidence.
J   A green wall proves nothing unless silence is impossible; G-T is what converts
    "no line said red" into "every line said OK". This is INV:I4/I9 applied to the
    apparatus itself, and it is the single node most of the BRIEF's audit weight
    rests on.
```

### 2.2 The per-family legs — claim, evidence, inference, leg-specific assumptions

One leg is worked in full (Family C/D, the load-bearing pair); the rest follow the same
five-slot pattern with their actual line names. Every Sn is a *retrievable pointer* —
instrument name + DerivationRecord hash + substrate + Frontier — never a prose "it
passed" (GSN Solution semantics; ADR-0013 Rule 5: the artifact, not the claim).

**G-C/D (worked leg) — "Derived validity is sound, and every consumption of a defeated
antecedent is flagged":**

```
G-C  "At Frontier F: the in-force set, head-resolution, and question status are exactly
      the defeater-closure of the record; no consumer judgment (enacts-soundness,
      stale-debt) reads T_event as T_now unflagged."
S-C  Two independent producers + bit-identical agreement + adjudicated-fixture
      reproduction.
Sn1  ledger_tnow.lp derivation, DerivationRecord {engine+version, config, EDB hash,
      program hash, output hash} — marriage A.4 shape.
Sn2  ledger_floor.py derivation (single-statement SQL, code-path-disjoint), same
      record shape.
Sn3  The differential line in the close manifest: verdict ∈ {AGREE | DIVERGE_BY_DESIGN
      (named) | DIVERGE_DEFECT | QUARANTINED}, registered as a declared observer line
      (A.5/AC7); AGREE means output hashes equal.
Sn4  Fixture reproduction: rows 25/27 (unsound derivation), the launder negative
      control, F42's row 31→27 miscite, the F44 triple, the banked s9–s14 four-arm
      numbers — each with its flipping mutation (marriage §5).
J-C  Why this supports the claim: a defect in EITHER encoding must either flip a banked
      fixture (caught by Sn4), break producer agreement (caught by Sn3), or be a shared
      blind spot — and shared blind spots are exactly what Sn4's ADJUDICATED (not
      synthetic) fixtures plus the F-A `answered` twin-blindness lesson bound: the two
      producers once shared the weaker answered-rule and the differential was
      structurally blind to it, which is why fixture ground truth is a separate leg
      from agreement, and why "AGREE" alone is never cited as fidelity.
A-C1 (leg assumption) The EDB both producers read is a single-frontier projection —
      TRUE only under quiescent export today (finding 1, §1.4); invalidating
      condition: any concurrent writer during export. Propagates to: G-C, G-D, G-T's
      substrate declaration.
A-C2 The F10 abstraction argument (§1) holds — G-C claims validity over the RECORD's
      structure, not over prose content. Invalidating condition: any §1.2 row's
      direction argument refuted.
```

**The remaining legs, same pattern (claim → lines → leg assumptions):**

- **G-A (record integrity, T_event):** append-only held, every edge resolves backward,
  no orphan/alias surface, delivery↔freight byte-identity. Lines: `soundness`,
  `close_sweep`, `verify_delivery_freight`, the id-backward acyclicity check (also the
  license for A6's stratification claim — one check, two consumers, cited not
  duplicated). Leg assumption: the write-boundary triggers were armed and unmodified all
  session (A4 below).
- **G-B (currency & contemporaneity):** M-trigger gap detection against the acts stream;
  citation currency; assumption expiry. Lines: `contemporaneity`, `observed_currency`,
  `read_currency`, the `ledger_assumes` expiry closure. Leg assumptions: the trusted
  clock (A2 — OPEN); cross-stream ordering close-time-bound (D13); warning-polarity for
  currency (D14: a currency flag never gates, a gap verdict may RED the close).
- **G-E (obligation & independence discharge):** every obliged row is DISCHARGED /
  UNDISCHARGED / REFUSED-AND-TAUGHT / WAIVED(row) — never silently open. Lines: the
  kernel write-time gates (e17 stamps, RULING:42's grandfathered template), `review_
  fixpoint`, `review_without_detail`, `core_a` probes. Leg assumptions: attribution
  lives kernel-side, NOT in the EDB (§1.2 row 5) — this leg's evidence is SQL-side by
  design; stamp-secret arrangements per RULING:43; **cross-session obligations are
  UNREPRESENTABLE as designed (OQ1) — see U1.**
- **G-F (claims-vs-acts differential):** every mechanically-detectable divergence
  between what was ledgered and what was done is surfaced with an adjudication slot.
  Lines: `cite_check`, `coverage_audit`, unledgered-span/unbound-row consumers,
  `stale_enactment_debt` (file-granular). Leg assumptions: transcript parser coverage
  (the discovery-completeness obligation — parity proves old formats parse, not that
  new files are found); acts-substrate originality between act and ephemera-persist
  (critic §4's I1 window) — pre-registered, not waived.
- **G-G (apparatus self-judgment):** G-T plus DerivationRecord completeness, capability
  manifests, empty-model quarantine, **the review-queue debt line** (INC 1: open/aging
  unadjudicated flags on the face of every close — a green close over unread flags is
  the dressed-up-QED at system level and is thereby unrepresentable as green-without-
  a-number).
- **G-H (review residue routed):** everything the engine may not judge (content truth,
  MECE, J-noticing) is ROUTED with a queue reference, never verdict-ed. Lines: review
  queue counts + the adjudication landing surface (**U2 — wiring design owed, OQ9**).
  J: Family H is what makes "the engine covers X" unable to be misread off an absence —
  the non-derivability register is first-class vocabulary (I12 applied to the engine).

### 2.3 The assumption register — first-class nodes, each with its invalidating condition

Per GSN v3, an assumption is a node with its own truth-status; when one falsifies, every
goal it feeds is undermined *mechanically traceably*, not by re-reading prose. The
registry's `assumptions[]` field (inc-0 §1.1, INV:I7 applied to the engine) is the
machine home; this is the authored content for it.

| # | Assumption | Feeds | Invalidating condition (what to watch) | Status |
|---|---|---|---|---|
| A1 | Single writer; exports/closes run against a quiescent record | G-C/D, G-T, every Frontier stamp | any concurrent session or live hook writing during export (finding 1 forecloses the export half mechanically when fixed; multi-writer semantics remain OQ14) | HELD-BY-PRACTICE, unowned in design |
| A2 | The evaluation clock is trustworthy (Part-11: "a clock the user cannot alter") | G-B expiry, C_t families, contemporaneity lags | clock skew/adjustment on the DB host; pinning `now` in the Frontier makes replay exact, NOT the clock honest | **OPEN — OQ8, maintainer** |
| A3 | Substrate resolution is correct (the named target is the read target) | every leg | ledger_target SSOT drift; the fc18 class (instance-pinned instrument); mitigated: target-resolved, RED on unregistered | HELD, mechanized |
| A4 | The kernel write-boundary triggers were armed, unmodified, and covering for the whole session | G-A, G-C/D (quotation validity, §1.2 row 4a), G-E gates | schema migration mid-session; a superuser bypass; fence defects (the finding-45 class: privilege verification must cover the whole trigger chain) | HELD; continuous-arming evidence is owed (a close line asserting trigger-set hash = frozen spec hash would mechanize it — candidate, stand-in) |
| A5 | The threat-model scope (C2) matches reality | G-F, the residual register | evidence of active instrumentation-evasion would void the pre-registration and demand a scope re-ruling (maintainer) | DECLARED |
| A6 | Engine integrity: stratified program, unique model, runner raises on non-solved, grounding witnesses | G-C/D | a rule edit introducing recursion through negation (the acyclicity/class checker catches the EDB side; the mechanical class checker — INC 3 — the rule side); an unmatched body predicate before INC 3 lands | HELD for the as-built set; INC 3 closes the class |
| A7 | The J-boundary: gap-detection guarantees quantify over M-triggers only | G0's completeness clause | reading "complete" as covering judgment-triggered entries (G3/G10/G15/F2-recognition) — the BRIEF §4 scoping, restated so no consumer imports the stronger reading | DECLARED, permanent |
| A8 | Append-only holds at the substrate (no in-place mutation reached the record) | G-A, everything downstream | superuser DML outside the boundary; mitigated by the acts/gate journal cross-check (G-F) within its coverage | HELD-WITH-RESIDUAL (declared) |
| A9 | The registry/manifest toolchain itself is sound | G-T, S0's quantifier | the meta-toolchain negative controls failing to fire (never-invoked close indistinguishable from green would void G-T) | HELD once INC 2's controls land; interim: the F49 line-accounting in close_manifest, seen-red |

### 2.4 Undeveloped goals — shown, not hidden

GSN's rule: an open goal is displayed as open, or the case lies by omission.

- **U1 — cross-session obligation carry-over** (OQ1, Fable): G-E is session-scoped; the
  BRIEF's central obligation shape (approval in one session, discharge in another) is
  unrepresentable as designed. Until solved, G-E's claim is explicitly per-session and
  the conformance sheet says so.
- **U2 — adjudication-loop wiring** (OQ9): where a Family D/F/H ruling lands, its
  id/Frontier semantics, re-derivation churn. Until designed, "routed" in G-H means
  "counted in the queue," not "guaranteed adjudicable in place."
- **U3 — law epochs / retroactivity** (OQ2): judgments citing laws over pre-law records.
- **U4 — decades-scale retention incl. archived solver versions** (OQ5): the case's
  Sn pointers are retrievable *today*; INV:I11's "re-runnable by an inspector decades
  later" is a plan owed, not a property held.
- **U5 — G12 access events on the judgment store / G14 security-scope declaration for
  the engine's new surfaces** (OQ6/OQ7): assessed-or-declared, currently neither;
  RULING:43 discharges only the stamp-secret corner.
- **U6 — the F10 acceptance leg** (§1.3(e)): this document's own sibling argument is
  DRAFTED-UNACCEPTED until the ratification act and the non-Fable review exist.

### 2.5 Why this is an argument and not a talisman — the audit walk

A reader (or the deductive engine itself, one increment hence — the tree above is
deliberately ledger-shaped: nodes with typed edges, ids, and truth-status, storable and
re-derivable like any other judgment) verifies the case by walking, not by trusting:

1. G-T first: did every mandatory line run, on the declared substrate? (Non-zero exit /
   quarantine accounting — mechanical.)
2. For each family leg: does each Sn pointer dereference — instrument output +
   DerivationRecord hashes present, fixtures reproduced, mutations flipped? (A verdict
   whose artifact cannot be produced is no verdict — ADR-0005 Rule 9 posture.)
3. For each assumption A1–A9: is its invalidating condition currently false? Any TRUE
   invalidating condition marks every downstream goal UNDERMINED — the propagation is
   edge-following, not judgment.
4. Read the disclaim list BEFORE acting on the green (§2.6) — the case's scope
   self-disclosure (INV:I12) is part of the case, with equal prominence (INV:I4's
   equal-prominence-for-negatives, applied to meaning rather than results).

Step 4 is the anti-talisman clause: "proved in clingo" becomes a *scoped* claim — proved
WHAT (the family verdict), OVER what (the emitted fact families), AT what frontier,
UNDER which assumptions, and NOT meaning the six things below.

### 2.6 The disclaim list — what a fully-green close does NOT support

Stated as first-class content, not fine print. A green G0 does **not** claim:

1. **Content truth.** No statement's factual correctness, no rationale's adequacy, no
   citation's semantic fit (Family H; the ids-not-text abstraction, §1).
2. **Content-level currency of IN-FORCE rows.** In-force = not-whole-row-superseded. A
   row may stand with a load-bearing clause defeated (FIND:F44); the defeat is flagged,
   its severity is not mechanically judged (§1.2 row 4a).
3. **Completeness over judgment-triggered entries.** An unnoticed hazard, an
   unrecognized assumption, an unfiled G10 produce no missing-entry signal (A7; BRIEF
   §4's M/J scoping — the guarantee's reach is M-triggers).
4. **Conduct outside the perimeter.** F38: what never touched the boundary was never
   recorded; the engine derives over what the record captures, full stop.
5. **Subject honesty as a disposition.** N=1 apparatus lessons; the pilot is an
   apparatus-quality argument, never a statistical or characterological claim about any
   model — and the census/coverage lines are encoding-coverage, never detection-power
   (D20).
6. **Security, competence, timing.** G14 beyond the declared scope, G13 competence
   records, F14 WCET — declared exclusions with reasons in the conformance map, not
   covered claims.

---

## 3. Honest limits of this document

- **Common-mode authorship.** The F10 direction table, the F12 tree, both producers it
  argues about, and most of the fixtures share one author-mind and one model family.
  The document names its own attack surface (§1.3(e), §1.2's "conservative" cells) and
  the acceptance leg is left OPEN rather than self-certified — but a Fable-class
  argument about Fable-built artifacts inherits the panel's common-mode caveat in full.
- **The direction analysis is against the AS-BUILT rule set.** Every admitted judgment
  changes the quantifier of §1.2. The registry hook (inc-0 §1.1 `assumptions[]` +
  admission protocol) is where this argument stays current: **admission of any judgment
  whose body reads a fact family or argument named in §1.2 items 4–9 requires updating
  the F10 row first** — proposed here as an admission-protocol clause, for the
  maintainer's ratification, so the argument decays loudly instead of silently.
- **No lab-data laundering.** Nothing above argues a substrate demand from absence in
  our runs; where scope was needed, the BRIEF was cited as the authority (standing
  rule). Conversely, no BRIEF row is claimed discharged beyond what §1.3(d) names.
- **This is a SEED.** Its F12 tree has one fully-worked leg and seven patterned legs;
  full instantiation (every Sn with live hashes on a real close) is build work,
  deliberately not faked here with placeholder hashes.

## 4. Open items, each with an owner class (silence forbidden; the register is the anti-silence)

| # | Item | Source | Owner |
|---|---|---|---|
| 1 | Fix the exporter's snapshot atomicity (single read transaction / pinned max id); precondition for INC 2 Frontier stamps and any T1 EDB consumer | §1.4 finding 1 | stand-in (mechanical); Fable review of the fix's frontier semantics |
| 2 | Resolve the EDB signature divergence: emit `amends_scope_len/2` or correct the docstring; add `actor` to the capability vocabulary as declared-DEFERRED | §1.4 finding 2 | stand-in, one design decision flagged to maintainer in passing |
| 3 | Per-argument capability declaration for `entry/6` optional arguments (absent-column ≠ NULL ≠ `none`), or the `absent` atom; plus the interim admission-protocol clause barring status/concern/confidence-reading rules until it lands | §1.2 row 7 | stand-in at INC 2 (generator home); clause ratification: maintainer |
| 4 | The F10 acceptance leg: ratification act + non-Fable adversarial review of §1.2 (every "conservative" cell is a refutation target) | §1.3(e) | maintainer (act); any non-Fable model (review, as a committed consult) |
| 5 | Continuous-arming evidence for the write-boundary triggers (close line: live trigger-set hash vs frozen spec hash) | §2.3 A4 | stand-in (candidate line; RED threshold ruling: maintainer) |
| 6 | F12 full instantiation: the tree as generated ledger-shaped rows over the registry + live Sn hashes on a real close (the tree is designed storable; storing it is build) | §2.5 | stand-in after INC 2; Fable for the tree-as-judgment-family semantics |
| 7 | The trusted-clock declaration (A2), retention plan (U4), access events + security scope (U5) | §2.3–2.4, unchanged from inc-0 OQ5–OQ8 | maintainer (declarations); stand-in (drafts) |
| 8 | OQ3/OQ4 disposition: this SEED is their proposed discharge; they close only by the maintainer's scan, not by this sentence | inc-0 §7 | maintainer |

---

*No files modified but this one. Two findings filed (db/harness/005) at observation
time. No sub-agents. psql not touched for evidence reads beyond the findings filing;
every code fact above cites a file read this invocation.*
