# FABLE-SETUP-TUI-DESTINATION-STATE-SPEC — one typed answer to "what is this directory to autoharn?"

autoharn's setup TUI (the terminal wizard under `tools/setup_tui/` that walks an
operator through a sequence of screens to create — "birth" — a new autoharn
deployment into a destination directory) currently answers "may I use this
destination?" five different ways in five places. This spec, written for whoever
implements or reviews that wizard, replaces them with one typed classification and
one on-disk sentinel.

- **Status:** Proposed (Fable-authored; Track 2.3 of
  [FABLE-SETUP-TUI-FIELD-STRATEGY.md](FABLE-SETUP-TUI-FIELD-STRATEGY.md); build
  gated on maintainer reading of that
  strategy — the maintainer's commission item c is its verbatim seed).
- **Date:** 2026-07-21
- **Commission (verbatim, maintainer observation c):** "TUI fails if dest-dir exists
  (add a sentinel to target directory and create a function that tests whether it is
  compatible with autoharn)"

## 1. The defect class (ADR-0000 Rule 2)

**(a) The type.** Today the question "what is the destination's relationship to
autoharn" has five independent answers: `screen_fork_target` refuses on bare
`exists()` (both modes, no third mode for a deliberately pre-populated destination);
`screen_birth` checks nothing and trusts `state["dest"]` unchecked;
`screen_principals_authority`, `screen_signed_genesis`, `screen_boundary` each
re-implement an `isdir` probe; and `bootstrap/new-project.sh` `mkdir -p`s and merges
into any occupied directory that lacks `deployment.json`. The witnessed consequence:
in the 2026-07-19 field test the maintainer populated the destination
(`/home/bork/w/vdc/1/test/blank`, "the blank world" below) *around* the tool, while
the wizard's setup checklist — its per-item record of what each screen witnessed —
recorded "fresh dir WITNESSED". The foreclosing type is one closed classification,
computed at one Port (an explicit boundary function every consumer calls and none
re-implements —
[ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) P2; the
P-numbers in this spec are that ADR's nine numbered principles), consumed
everywhere:

```python
class DestKind(Enum):
    FRESH = "fresh"                        # absent, or an empty directory
    AUTOHARN_COMPLETE = "autoharn-complete"  # sentinel + deployment.json + legacy/led all present and consistent
    AUTOHARN_PARTIAL = "autoharn-partial"    # some birth evidence present, not all — an interrupted birth
    FOREIGN = "foreign"                      # non-empty, no autoharn birth evidence

@dataclass(frozen=True)
class DestinationState:
    kind: DestKind
    evidence: tuple[str, ...]   # the observed facts the kind was derived from, for teaching copy
```

**(b) The lapse.** Each screen was authored against its own local worry; no review
asked where the fact lived. This spec is the P1 conversion (ADR-0012's
single-source-of-truth principle: one home per fact), and §5's fixture set is the
mechanized recurrence-catcher
[ADR-0011](../law/adr/0011-mechanization-discipline.md) requires so the class stays
closed.

## 2. The sentinel

Birth writes `<dest>/.autoharn-world.json` (new-project.sh, at the same point it
writes `deployment.json`), content: `{"world": <name>, "run": <run id>,
"born": <ISO ts>, "autoharn_commit": <sha>, "schema": 1}`. The sentinel is the
*declared* marker; `deployment.json` + `legacy/led` remain the *behavioral* evidence.
Compatibility (the maintainer's requested test function) is
`classify_destination(path) -> DestinationState`:

- no path, or empty dir → FRESH.
- sentinel present, parseable, and `deployment.json` + `legacy/led` (the directory a
  born world carries its `led` ledger CLI in — the behavioral proof a birth
  completed) present →
  AUTOHARN_COMPLETE. A sentinel that contradicts `deployment.json` (different world
  name) is AUTOHARN_PARTIAL with the contradiction in `evidence` — never coerced
  (ADR-0002 Rule 2).
- any strict subset of {sentinel, deployment.json, legacy/led} → AUTOHARN_PARTIAL,
  `evidence` names what is present and what is missing.
- non-empty and none of the markers → FOREIGN, `evidence` samples up to 5 entries.

Existing worlds born before this spec have no sentinel: they classify from the
behavioral evidence alone (deployment.json + legacy/led ⇒ AUTOHARN_COMPLETE, and the
classifier's docstring says so). No retro-stamping of dust worlds (runs are linear).

## 3. One Port, every consumer

`classify_destination` lives in a new small module (`tools/setup_tui/destination.py`;
ADR-0007-conformant), imported at module top (no lazy imports). Consumers *replace*
their ad hoc probes:

- **screen_fork_target** switches on the kind: FRESH → as today; AUTOHARN_COMPLETE →
  teach re-entry (`--start-at`) vs re-birth-needs-teardown (existing copy);
  AUTOHARN_PARTIAL → existing partial-birth teaching; FOREIGN → the NEW third mode:
  show the evidence, and offer an explicit typed acknowledgment ("scaffold into this
  existing content") which sets `state["dest_accept_foreign"] = True`. No silent
  merge, no flat refusal — the blank world proves the use case is real.
- **screen_birth** refuses to queue the birth unless the classification (or the
  queued-this-session `dest_would_exist` fact) sanctions it — the currently-missing
  check. FOREIGN without the acknowledgment fact is a refusal that teaches.
- **principals_authority / signed_genesis / boundary screens** consume the same
  classification (their out-of-sequence guards keep their current copy, minus the
  private probes; `principals_authority.py`'s `legacy/led` probe folds into the
  classifier).
- **bootstrap/new-project.sh** gains the same closed decision: FOREIGN destination →
  refuse loudly unless `--accept-existing-content` is passed (which the TUI passes
  exactly when the acknowledgment fact is set). The current
  deployment.json-only refusal keeps its `--force` semantics for the AUTOHARN kinds.
  Shell-side classification is a minimal re-derivation of §2's rules (markers only,
  no JSON parsing beyond existence + world-name grep); the Python classifier is the
  authority and the shell's version says so in a comment (the floor ADR-0012 P7 —
  its cross-language wire principle: one authoritative definition, every other
  reader derives — permits when codegen is disproportionate; drift caught by §5's
  parity fixture).

## 4. Purity

The wizard's architecture (its pure-core spec,
[FABLE-SETUP-TUI-PURE-CORE-SPEC.md](FABLE-SETUP-TUI-PURE-CORE-SPEC.md)) splits every
run into a decision phase (screens ask and decide, no effects) and a commit phase
(the queued plan executes). Classification is a read-only probe — decision-phase
legal, same class as the existing preflight probes; the sentinel WRITE happens only
inside new-project.sh during a committed birth. No new decision-phase effects, so
`gates/setup_tui_purity_gate.py` (the mechanical check that the decision phase stays
effect-free) is untouched.

## 5. Witness set

- Unit fixtures: one per kind, plus the contradiction case and the pre-sentinel
  legacy-world case.
- Parity fixture: shell vs Python classification agree on the five witnessed shapes
  (fresh / complete / partial / foreign / legacy-complete).
- Red-then-green for the two closed defects: (1) screen_birth accepting an unchecked
  dest (red against pinned pre-fix module), (2) new-project.sh merging into FOREIGN
  content (red leg in a scratch dir).
- Scripted-smoke re-run for regression; the blank world itself (read-only) as a live
  classification specimen: expected AUTOHARN_COMPLETE-via-behavioral-evidence.

## 6. Out of scope

Teardown semantics; the open maintainer question of whether a failed
genesis-commission signature verification should hard-stop the birth ceremony
(today it records a REFUSED checklist row and continues); and any checklist-status
vocabulary change
([FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC.md](FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC.md)'s
scope). The screens' copy rework beyond the new FOREIGN mode belongs to the
strategy's Track 2.1/2.2 (typed UI elements and prompt-text extraction).
