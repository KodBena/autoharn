# Idris transcription consultation — record (2026-07-15, night)

Point-in-time consultation record, banked verbatim below the rule. Provenance: an Opus
consultation (maintainer's explicit dispatch and model choice — pure semantics-replication
leaves overconfidence no judgment surface), restarted fresh after the maintainer judged the
first brief's action-flavored sections had anchored it; the maintainer then instructed it
directly to install the Idris toolchain (left installed on the host, deliberately, for the
maintainer's own use) and machine-check the model. The checked artifact is
[Autoharn.idr](Autoharn.idr) (493 lines, elaborates under %default total, Idris 2 v0.7.0,
zero holes, zero postulates; three green fixtures + three failing-block refusal polarities
checked inside the file). Disposition (maintainer, ledgered): categorical documentation of
what exists; nothing is settled; kludgy-where-true is a first-class finding.

---

The transcription is done and machine-checked. Report follows.

---

## Idris transcription of the autoharn kernel semantics — findings

**Artifact:** `/tmp/claude-1000/-home-bork-w-vdc-1-autoharn/a857c93d-d154-4d01-b726-122ec07401fc/scratchpad/Autoharn.idr` (493 lines, one module).
**Checked status: CHECKED**, not paper-only — the whole file elaborates under `%default total` with **Idris 2 version 0.7.0**, exit 0, zero holes, zero postulates, on a compiler bootstrapped on this machine during the session. Witnessed: `idris2 --check Autoharn.idr` → clean, twice from a scratch build dir, with both the build-tree binary and the installed one. Both polarities witnessed inside the file itself (§7): three green fixtures construct, and three `failing` blocks that only type-check because the illegal shapes are *refused* at elaboration (a `failing` block errors if its body compiles). Sources read in full before transcribing: ADR-0000, ADR-0012, s15/s22/s29/s30 DDL, `ledger_tnow.lp`, `work_items.lp`, both ratified specs.

The one overall conclusion first: **this is not kludgy.** The kernel's semantics transcribe into Idris with less friction than I expected going in — several trigger disciplines become structural facts — and the places where the rendering fights the language are few, local, and each one is itself informative. Per-item:

### 1. Ledger as indexed append-only structure; kinds as a sum type — **faithful**

```idris
data Ledger : Nat -> Type where
  Lin  : Ledger 0
  (:<) : Ledger n -> Entry n -> Ledger (S n)

record Entry (n : Nat) where           -- common columns
  ...
  supersedes : Maybe (Fin n)           -- FK is the ONE write constraint
  payload    : Payload n

data Payload : (n : Nat) -> Type where
  PReview     : (regards : Fin n) -> ReviewDetail n -> Payload n
  PWorkOpened : (slug : Slug) -> (title : String) -> (parent : Maybe Slug)
             -> (composite : Bool) -> Payload n
  PWorkClosed : (slug : Slug) -> (res : Resolution) -> witnessTy res
             -> (disp : ReviewDisposition) -> reviewRefTy disp
             -> (strict : Bool) -> Payload n
  ...

witnessTy : Resolution -> Type         -- s22 work_shipped_requires_witness
witnessTy RShipped = NonEmptyText
witnessTy _        = Maybe NonEmptyText
```

Where the CHECK idiom and the constructor idiom say the same thing: the two-way shape CHECKs (`(kind='work_closed') = (work_resolution IS NOT NULL)`) *are* constructor argument lists — the SQL is hand-rolling a discriminated union and the ADR-0000 vocabulary transfers verbatim. One-way CHECKs become `Maybe` inside the licensed constructor; conditional CHECKs (shipped ⇒ witness, witnessed ⇒ ref) become dependent field types — a Π where SQL used a row predicate, and this is *witnessed refusing* in the red fixtures. Three structural facts come free that SQL pays triggers for: append-only is absence of syntax (no update/delete constructor exists), `one_row_per_insert` is inherent in `(:<)`, and every back-reference being `Fin n` makes "must resolve to an earlier row" plus acyclicity-of-all-closures unrepresentable rather than trigger-trapped (the third red fixture: `PReview 3 … : Payload 3` does not elaborate).

Where they genuinely cannot say the same thing, two places. (a) **Lineage evolution**: the kernel grows by additive `ALTER TABLE ADD COLUMN` deltas per sNN; an Idris sum type is closed — s29's three columns are a constructor *rewrite*, not an addition. The SQL CHECK idiom is compositional across deltas in a way constructors are not; a faithful "lineage of models" would be one module per sNN, each re-declaring the union. (b) The **epoch gate** (s29 sec-10): "disposition mandatory iff `NEW.id > migration_epoch`" is a shape conditioned on mutable operator state outside the ledger — expressible as a type index but only by threading a runtime value into the payload type; I left disposition unconditionally mandatory and note the divergence (the model renders the post-epoch steady state, not the migration accommodation). One deliberate non-fix: `work_depends_on` names its antecedent by slug and s22 deliberately leaves it danglable — so that field stays `Slug`, not `Fin n`; "upgrading" it would erase the `depends_on_unknown_slug` violations member the kernel explicitly keeps reachable.

### 2. In-force projection + reader typing — **faithful**, and the reader judgment lands unusually well

```idris
supersededIn : Ledger n -> (t : Nat) -> Bool   -- monotone: edge EXISTENCE only
inForce      : Ledger n -> (t : Nat) -> Bool   -- total by construction

record Projection (n : Nat) where …            -- constructor unexported in a
project : {n : Nat} -> Ledger n -> Projection n --   multi-module rendering

data HistoryLicense : String -> Type where     -- the closed allowlist, §2 of the spec
  LHashChain     : HistoryLicense "row-hash-chain: every row must chain, superseded or not"
  LLedRecent     : …
  LDuplicateOpen : …
  LWriteBoundary : …

CurrentReader n a = Projection n -> a                                  -- cannot name Ledger
HistoryReader n a = {reason : String} -> HistoryLicense reason -> Ledger n -> a
```

Totality is free (fold over finitely many rows; ASP pays a comment for the same fact, SQL pays nothing). The ratified reader judgment becomes a *scope* fact: a current-truth reader's signature cannot mention `Ledger` at all, and a history reader must present a license drawn from a closed indexed type — adding a history reader is adding a constructor, so the allowlist amendment IS the diff. This is the spec's allowlist gate expressed as unrepresentability rather than as a `.detect` scan, and it is the single place the Idris rendering is *stronger* than the shipped mechanism at zero contortion.

### 3. Work-item event grammar as indexed machine — **faithful-with-encoding-noise, and one transcription finding**

**Finding (kernel wins over the brief's parenthetical):** the write-boundary grammar is *not* linear open→claim→close, and close does *not* require claim. `validate_work_item()` (s22→s30, read in full) refuses exactly: duplicate open (raw-history read — burned slug), later-event-on-unopened-slug, dangling/cyclic parent at open, blocks-close self-edge/dangling/cycle, post-epoch disposition-silent close, strict+deferred, and strict-with-blockers. It does not require a claim before close, and does not refuse a second claim or a second close row. Linearity lives in the *projection* (`work_item_current`'s latest-event `DISTINCT ON` fold), not the write boundary. The model transcribes both layers separately; a single indexed state machine `Open → Claimed → Closed` would be the model lying about the kernel.

```idris
data ValidAppend : Ledger n -> Entry n -> Type where
  VOpen  : (0 fresh : So (not (everOpened l s)))          -- RAW read: slug burned
        -> {auto 0 isOp : So (isOpenOf s e.payload)} -> ValidAppend l e
  VLater : (0 opened : So (everOpened l s))
        -> {auto 0 isLater : So (isLaterEventOf s e.payload)} -> ValidAppend l e
  VProse : {auto 0 notWork : So (not (isWorkPayload e.payload))} -> ValidAppend l e

append : (l : Ledger n) -> (e : Entry n) -> (0 ok : ValidAppend l e) -> Ledger (S n)
```

Slug-burning renders with no new mechanism: the freshness proof quantifies over the **raw** ledger (`everOpened` ignores supersession), so a retracted open still blocks forever and there is simply no re-open constructor — the ratified fork appears in the model as *which structure a proof obligation quantifies over*, which is the reader-type judgment (item 2) showing up inside the write boundary exactly as the spec's allowlist says it should (`LWriteBoundary`, `LDuplicateOpen`). Encoding noise: the trigger is a smart constructor (`append` as sole export), which is a module-abstraction convention rather than the DDL's hard construction-time surface — same guarantee, different enforcement register.

### 4. Obligation AND-tree as derived fold; composite discharge as a read — **faithful-with-encoding-noise** (two named pieces)

```idris
edgesOf        : Ledger n -> List (Slug, Slug)  -- s28 parent ∪ s30 blocks-close (walked against its column names)
reach          : (fuel : Nat) -> … -> List Slug
strictBlockers : {n : Nat} -> Ledger n -> Slug -> List Blocker   -- empty iff resolved; NO stored verdict
effectiveState : … -> EffectiveState            -- composite: a READ of strictBlockers; zero children => open
```

The one-conjunction discipline (ADR-0012 P1) transcribes directly: `effectiveState` calls the same `strictBlockers` the strict-close premise uses — one home, two readers, cannot drift. The vacuous-truth foreclosure is a pattern-match (`composite && hasChild` guard). Noise piece 1: **termination.** SQL's recursive CTE terminates on any graph by set semantics for free; `%default total` demands a measure, so the walk carries fuel = row count. Honest but audible. Noise piece 2: the review leaf (`deferredUndischargedIn`) is an **oracle stub returning False** in the checked file — the real correlation (review.regards = close row id, distinct actor, un-superseded) needs absolute row ids threaded through the fold; declared in-file as a stub, not smuggled. What the model does preserve, deliberately: `hasCloseIn` reads **raw** closes while the review leaf is supersession-aware — the composite spec §3b's named blind spot, visible in the model as two different quantification domains inside one calculus. Transcribing the blind spot rather than silently fixing it is the point of the exercise.

### 5. Uniform retraction, reinstatement-free — **faithful, and provable rather than merely testable**

The precise rendering of "superseding the superseder does not revive the victim": `supersededIn` is *monotone* — it quantifies over edge existence only, never the superseder's own status — so supersededness is stable under every ledger extension. Proved, not asserted (checked, 3-line proof):

```idris
supersededStable : (l : Ledger n) -> (e : Entry n) -> (t : Nat)
                -> supersededIn l t = True -> supersededIn (l :< e) t = True
```

The spec's acceptance bullet ("reinstatement-free witnessed") is a per-world fixture; here it is a theorem over all ledgers. Honest counterpoint: Idris does **not** make the rejected semantics unrepresentable. Genuine reinstatement (`in-force iff no in-force superseder`) is recursion through negation — outside plain SQL anti-joins and stable-model territory for ASP, but in Idris it is a perfectly ordinary total function, since ids are finite and the recursion runs upward well-foundedly. So the spec's "not expressible" line is a fact about the SQL producer's expressive floor, not about definability; what Idris offers instead is *legibility of the fork* (a visibly monotone definition vs visible recursion-through-negation) plus the stability theorem. Keeping readers off the rejected side would take module abstraction over the edge set — discipline again, at a different layer.

### 6. Dual-producer differential — **partially expressible, honestly bounded**

```idris
record DualProducers (n : Nat) where
  sqlFloor : Ledger n -> List Nat    -- opaque: Postgres/recursive CTEs
  aspSide  : Ledger n -> List Nat    -- opaque: clingo/ledger_tnow.lp

InForceSpec : {n : Nat} -> Ledger n -> List Nat -> Type   -- the ONE spec both answer to
Agree : {n : Nat} -> DualProducers n -> Ledger n -> Type
Agree p l = p.sqlFloor l = p.aspSide l
judge : (p : DualProducers n) -> (l : Ledger n) -> Dec (Agree p l)
```

Two functions with one specification type — yes, and that is the part worth having: the model states, in one place, exactly what both producers are held to. What it cannot say: **producer independence**. Giving the producers Idris bodies would replace two independent substrates with two functions sharing one compiler, one stdlib, one author — a proof `sqlFloor = aspSide` would then certify that my two transcriptions agree, which is the "twins agree; agreement is not fidelity" failure `ledger_tnow.lp`'s own F-A note documents from experience. So both stay black boxes, `Agree` is decidable per world (`judge` mirrors `./judge`: a runtime observation, not a theorem), and independence remains what it is in the repo — a provenance fact, outside any type system's reach.

### Honest limits

- **Stamp HMAC is runtime trust, fully mocked.** `Stamp` is opaque; `stampValid` is a boolean oracle field. The load-bearing property — the subject role cannot read the secret (REVOKE + SECURITY DEFINER) — is a *privilege* boundary; Idris types model data shape, not who can read what at runtime. Also unmodelled: `set_actor()` stamping from connection identity ("never self-declared") is an authentication fact, not a shape fact.
- **Trigger-time visibility is invisible — the model is cleaner than reality here, which is itself a divergence.** s29 deliberately checks the root's own review leaf against `NEW.*` because a BEFORE INSERT trigger cannot see the row being inserted; in the model the candidate entry is just an argument, so the whole hazard class (and its careful SQL workaround) has no counterpart. A reader of the model alone would never learn that constraint exists.
- **Concurrency and MVCC: absent.** The model receives a total append order as given (the id sequence). Two concurrent writers both passing a freshness check, serialization of trigger reads, `search_path` capture — all outside. The kernel's "id is the order, never ts" discipline is trivially absorbed (ts never enters any ordering type), which is faithful but unearned.
- **The epoch gate and migration accommodations** (s29 sec-10, `.accommodate.sql` files) are operator-state-conditioned shape rules; the model renders the steady state only (see item 1).
- **Closed-ness of the model is manual.** The transcription covers s15+s22+s28(edges only)+s29+s30 and the two specs; s17/s21/s23–s27 (stamps beyond opacity, session distinctness, hash chain, contemporaneity) are named exclusions, not silences. The hash chain in particular would transcribe naturally (an index threading `prevHash` through `(:<)`) but was out of the commissioned six items.
- **Grade-is-computed** (s29 `discharge_grade`, "never writer-asserted") is only half-rendered: the field sits in `ReviewDetail`, and keeping writers from supplying it needs the same module-abstraction move as the smart constructor — convention in a one-file sketch.

### Toolchain (kept, per your request)

- Installed: `~/.local/idris2/bin/idris2` (Idris 2 v0.7.0, Chez backend via your system `scheme` 10.3). `export PATH=$HOME/.local/idris2/bin:$PATH` and it works with default lib paths — witnessed checking the model clean.
- Build tree kept at `~/idris-toolchain/Idris2-0.7.0` (382M; `build/exec/idris2` also works, needs `IDRIS2_PATH` to the libs). `~/idris-toolchain/csv10.1.0` (37M) is my now-redundant Chez source build — safe to delete since you installed the distro chezscheme; left in place rather than deleted unilaterally.
- The long stall you asked about was mine, not the build's: I parked several background waiters on `pgrep -f 'make install'`, and each waiter's own command line contained that string, so they kept each other "running" after make had finished. Caught via `pgrep -af`, killed, and the install then completed in seconds. Filed here as the session's own snag, on the record.

<!-- doc-attest-exempt: point-in-time consultation record, banked verbatim. -->
