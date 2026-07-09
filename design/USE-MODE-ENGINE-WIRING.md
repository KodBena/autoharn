# USE-MODE ENGINE WIRING — toy pilot (spec, 2026-07-09)

Status: DESIGN, ratified mandate. Maintainer ruling 2026-07-09: the deductive engine is the
project's point (design/possibly-addressable-concerns.md:44-47) and MUST be reachable from
Use-mode; the toy pilot wires it first. Law read in full for this spec: ADR-0000, ADR-0012,
ADR-0013. Grounding: read-only engine reconnaissance, session be693afb (engine/ledger_edb.py,
ledger_floor.py, ledger_differential.py, clingo_run.py, lp/*, close_manifest.py, live toy
queries).

## The defect class this forecloses (ADR-0000 closure statement)

Two defects were found in passing, both instances of ONE class — a kernel deployment's names
re-authored by hand at N consumers instead of derived from one home (ADR-0012 P1; cancers B/F):

- `engine/ledger_edb.py` `resolve()`: unknown target names silently fall through to
  `db="epistemic", schema=<name>` — `resolve("toycolors")` targets the WRONG DATABASE with no
  error (the exact silent-fallback ADR-0002 forbids).
- `engine/ledger_edb.py:227`: kernel-shape detection tests the literal relation name
  `"kernel.principal"`. Toy's kernel schema is `toycolors_kernel` (a `-v kern` parameter by
  design), so against a real, populated toy ledger the engine silently EXCLUDES the whole
  `regards`/review/obligation family while claiming a declared exclusion — the F49 lesson
  recurring in the module built to prevent it. Sibling of open finding 51
  (`instruments/ledger_target.py:37`, same literal plus `name='subject'`).

**Invariant.** Every consumer of a deployment's names (db, ledger schema, KERNEL schema)
derives them from one home; a name unknown to that home is refused loudly, never silently
mapped to another database.

**Quantification universe** (all current consumers, enumerated):
`engine/ledger_edb.py` (`_SPECIAL`, fallthrough, the `kernel.principal` literal);
`instruments/ledger_target.py` (`_SPECIAL`, `_KERNEL_SUBJECT`); `engine/ledger_differential.py`
/ `close_manifest.py` (target-name args); toy-project `led` + `.claude/settings.json` (env
defaults — already correct, out of this diff); `WALKTHROUGH.md` `-v` vars (prose, out of this
diff). Axes: db name, ledger schema, kernel schema. Named as NOT covered here (filed, not
silent): (a) the apply/arm step emitting a machine-readable deployment record the registry
could ingest (friction-log item; future arm work); (b) finding 51's `name='subject'` principal
assumption (its own remediation; the new home must not import it); (c) toy-side env defaults
(already one home per file, working).

**Denomination.** Names are opaque strings owned by the deployment record; no consumer
re-types them, no schema name is a literal in engine/instrument code.

## Design

1. **One home: `engine/targets.py`** — stdlib-only leaf module (top-of-file imports only; the
   lazy-import gate applies). A frozen `TargetInfo(db, schema, kern)` plus `resolve(name)`:
   - explicit registry: `nla`, `e15`→vsr, `e16`→hvn, `e17`→wmb, `e18`→qbx (all `kern="kernel"`),
     **`toy` → TargetInfo("toy", "toycolors", "toycolors_kernel")**;
   - scratch pattern `^s\d+$` → `("epistemic", <name>, "kernel")` (the banked lineage targets
     s10–s13 keep working);
   - env override `LEDGER_DB`/`LEDGER_SCHEMA`/`LEDGER_KERN` (full, as today, plus kern);
   - anything else → loud `ValueError` naming the known targets (forecloses the silent
     epistemic fallthrough).
   Executor MUST read `engine/verify_registry_parity.py` first; if parity is pinned against an
   external repo's copy, extend without breaking that contract and report the constraint — do
   not improvise around it.
2. **`engine/ledger_edb.py`** consumes `targets.resolve()`; kernel-shape detection becomes
   `t.has_relation(f"{target.kern}.principal")` — derived, never a literal.
3. **`instruments/ledger_target.py`** consumes the same home (its `_SPECIAL` dissolves into
   it). `_KERNEL_SUBJECT`'s schema literal is parameterized from `target.kern`; the
   `name='subject'` semantics stay as-is (finding 51's scope), explicitly not regressed.
4. **`toy-project/judge`** — a small operator/agent-invoked script beside `led`, same style
   (env-overridable): runs `engine/ledger_differential.py toy --retain`, prints the closed
   verdict vocabulary (AGREE / DIVERGE_BY_DESIGN / DIVERGE_DEFECT / QUARANTINED), exits
   non-zero on DIVERGE_DEFECT/QUARANTINED. **Observer-first** (M-2 posture, matching
   close_manifest's DECLARED_OBSERVERS): not wired into any gate; whether it ever becomes
   gating is a maintainer decision, filed when the first real divergence is seen.
5. **Programs in scope now:** `ledger_tnow` (+ SQL-floor differential) and `ledger_support`
   (+ floor). `ledger_assumes` runs engine-only (no floor exists, by declaration) — reported,
   not differentialed. **Named deferrals:** the acts layer (toy has no act stream; findings
   49/50 are open exactly there) and DTO (apparatus-authored scratch lineages only, per its
   own header). Stamp vocabulary: the EDB deliberately carries no stamps; a defeasible
   independence judgment at the ASP layer is future engine vocabulary — filed in BACKLOG, not
   smuggled in here.
6. **Provenance:** every toy run uses `--retain`; DerivationRecords land under
   `engine/docs/ledger-marriage/derivations/toy/` and are committed (the auditability clause —
   this directory has never existed because --retain was never used; first use starts the bank).
7. **Witness protocol (ADR-0013 R5):** unit/differential tests against the banked scratch
   targets first; the live toy witness runs ONLY on a quiescent ledger (the differential's two
   producers read at different instants — a concurrent insert fabricates divergence), i.e.
   after the currently-running exercise/window-close agents finish. Acceptance evidence = the
   first toy DerivationRecord pair + verdict, plus one re-witness of the `--drop-record`
   QUARANTINED negative control against toy.
8. **Findings hygiene:** the `ledger_edb.py:227` defect (engine sibling of 51) is filed in
   `harness.finding_open` as found-and-fixed-same-increment if the findings ledger accepts the
   write; if permission-denied, STOP on that step and record in BACKLOG.md instead — never
   route around.

## What this deliberately does not do

No gating (observer only). No acts/DTO wiring. No stamp-aware ASP vocabulary. No WALKTHROUGH
apply-step record emission. No fix of finding 51's principal-name semantics. Each is named
above with its home; none is silently absent.
