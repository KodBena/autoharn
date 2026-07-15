# instruments/ — retrospective audit instruments (and deployable-hook seeds)

The series' first *deliverable* components, distinct from the experiment scaffolding: they
consume the witnesses (Postgres statement log + PreToolUse audit log + the ledger) and answer
the two questions the series has isolated. Both are read-only and were validated against e6's
independently-known facts before use.

## `contemporaneity.py` — the batch-logging gap-detector (F6/F10/F18)

Measures whether a ledger was kept *as you go* or *batch-reconstructed*, from two orthogonal
signals:

- **TIMING** — cluster inserts by temporal proximity (`GAP_S`); `batched_row_frac` = fraction of
  rows in a multi-row burst. The printed verdict prefers the Tier-2 per-entry lag distribution (the
  gold signal) when a tool-call log exists, and only falls back to `batched_row_frac` otherwise
  (burst structure alone can mislead — a mostly-batched run with trailing singletons is still
  batched; link-6 issue B).
- **VEHICLE** — `bulk_max` = largest group sharing an *identical* insert ts; `>1` ⇒ a bulk
  `psql -f`/multi-row load, `=1` ⇒ individual INSERTs.
- **Tier 2** (audit-hook sessions) — per-entry lag (insert ts − enacting Write/Edit ts) and
  ordering violations (a `snag`/`revision` logged *after* the act it resolves — the F18 defect).

Validated on e6/s7: 4 bulk bursts (7/6/4/5), `batched_row_frac`=1.00, median lag 51s, and the one
ordering violation is row 17 (the D4 contest snag, +47s after its test re-judge) — the F18
finding, machine-derived.

## `read_currency.py` — the mutable-source currency check (F16/F17/F20)

The rule banked from the retired two-read paradigm: a citation of mutable source S is GREEN iff
the citing role read S with **no write to S between that last read and the citing act**; else it
FLAGS. Fails safe (a missing re-read or an intervening write both flag). Validated on e6:
the actual run greens (re-read at 05:54:20, after the 05:46:06 correction); a synthetic
no-re-read counterfactual flags STALE (falls back to the 05:26:53 turn-1 read, which the
correction post-dates). This is the mechanically-checkable half of F20 — it cannot prove *use*,
only refuse a citation resting on a stale read.

## `sweep-results.txt` — the s1..s7 contemporaneity sweep + reading

Corrects the "always batches / 3-of-3 under the mandate" framing: vehicle and timing are
separable, and contemporaneity is high-variance under the identical mandate (s7 batched, s6
near-contemporaneous). s4 (individual inserts, still time-clustered) is prior evidence that e7's
bulk-vehicle removal need not by itself yield contemporaneity — i.e. e7's workflow-limb is live.

## `observed_currency.py` — reference truth at the moment of citation (F42, e13)

The e12 law made mechanical: a citation is trustworthy only if the cited id was OBSERVED by the
subject — in an id-projecting read-back whose kind-filter admitted it — within the window before the
citing INSERT. Consumes the role-attributed statement log (off-host tee.log via `--log=PATH`, or the
`/home/bork/pg_log` glob) × the ledger. Models the exact e12 discriminator (kind-filtered read-backs
hid rows 27/28; RETURNING was piped to /dev/null). Fail-SAFE: RETURNING is NOT counted as an
observation (discarded/held-in-memory currency is a lying comfort). Replaying s12 flags `enacts(31->27)`
(the miscite) and passes `supersedes(29->26)` / `supersedes(30->6)`. Kind-INDEPENDENT, so it closes
the hole `soundness.alias_surface` leaves open (which catches a miscite only when the wrong target is
a non-decision). Usage: `observed_currency.py --log=<tee.log> [--log=…] s12`.

## `core_a.lp` + `run-core-a.sh` — the corpus-consistency k-phase check (e13)

The Core-A satisfiability phase structure (external corpus-consistency-RESULT, consult 17 §5.2), the
standing evidence behind the two s13 waiver rows: the corpus is consistent as a theory; its
satisfiability is parameterized by principal cardinality/partition. `run-core-a.sh` runs the sweep
(k=1 UNSAT; k=2 SAT technical; SoD triple needs k=3; financial needs 2 orgs). Strict kernel only —
medium-confidence and J-triggered corpus entries are deliberately excluded.

## amends-awareness (e13) in `soundness.py` and `stale_enactment_debt.py`

`soundness.py` gained a `clause_defeat(A,T,scope)` readout — the F44 aspectual gap made measurable
(a held row whose specific clause is defeated by an in-force `amends` edge while it survives whole-row
supersession), with moot/withdrawn variants. `stale_enactment_debt.py` gained CLAUSE-STALE debt
(a file unlocked under an antecedent whose clause was later amended) and an UNREACHABLE-BY-DEBT
readout (F45: no-antecedent tickets, whose stale-debt silence is structural, not a clean bill). Both
degrade to silence on the pre-e13 schemas (amends exists only on the s13+ lineage), so the closed
historical schemas are read unchanged.
