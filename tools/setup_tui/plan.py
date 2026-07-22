"""tools/setup_tui/plan.py -- THE PLAN: the reified program a pure decision phase builds
(design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md §2.2, commission ledger rows 1823 point 2 / 1825).

PHASE-1 FOUNDATION MODULE (builder's report, ledger rows 1823/1825 commission): this is the
typed core of the pure-core restructure -- the plan the decision phase (screens 1-11) builds and
the commit boundary (tools/setup_tui/commit_executor.py) consumes. It is landed standalone,
before tools/setup_tui/screens.py is rewired to use it, because the rewire is the large remaining
body of work (every screen's live-effect call site becomes a `Plan.append(...)` instead) and this
module is the stable contract that work is written against. Nothing in tools/setup_tui/screens.py,
app.py, runner.py, or ui.py imports this module yet -- landing it changes no existing behavior and
breaks no existing fixture (ADR-0004 minimal-touch: new file, zero edits to working code).

THE SHAPE (spec §2.2, maintainer clarification ledger row 1825 -- "side effects pushed to the
boundary via continuations, in its plain operational sense"): a `Plan` is an ordered list of
`PlanEntry` objects. Each entry carries:
  - the exact act (`CommandAct` / `WriteAct` / `BackgroundAct` -- one dataclass per
    `tools.setup_tui.runner` choke point: `run_command` / `write_file` / `start_background`),
  - its checklist screen + item name (so the commit executor's checklist rows are the SAME
    (screen, item) pairs the pre-commit WOULD-DO rendering already used -- WPC2's argv-parity
    property depends on this),
  - its lesson line (the propaedeutic text a screen would have `ui.say`'d inline; deferred here
    to render at EXECUTION time, "where its real outputs are", per spec §2.3),
  - its bindings-affecting name (`produces`), if this entry's real output resolves a later
    `Hole` -- e.g. a `led decision` write whose stdout carries a row id a later entry's argv
    needs.

A value unknowable before execution -- a row id parsed from a prior entry's real output -- is a
typed `Hole` (spec §2.2: "rendered symbolically ... and resolved only at commit ... a hole is a
CONTINUATION of a prior entry's output, represented, never faked", citing ADR-0000's ban on a
fabricated value standing in for a real one). `Hole.symbol()` gives the symbolic form
("<row-id of step 5>") the pre-commit WOULD-DO table shows; `Hole.resolve(bindings)` gives the
real value once `bindings[self.of]` exists (populated by the commit executor after `of`'s own act
has actually run).

WHY A SEPARATE ARG TYPE (`Arg = str | Hole`) AND NOT A PLAIN F-STRING: an f-string spliced with a
not-yet-known value has no honest way to represent "not yet known" -- it would need a sentinel
string, which is exactly the fabricated-value ADR-0000 forbids (a `"<pending>"` marker that could
collide with real argv text, or worse, silently execute if a caller forgets to substitute it
first). `Hole` is a first-class value: `CommandAct.render()` renders it symbolically,
`CommandAct.resolve()` raises `KeyError` (a loud, typed failure -- ADR-0002) if asked to resolve
before its binding exists, and only the commit executor ever calls `resolve`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable, Union


# --------------------------------------------------------------------------------------------
# Holes: a typed placeholder for a value only the act's own prior execution can produce.
# --------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Hole:
    """A value unknowable before `of` (a `PlanEntry.produces` name) has actually executed.

    `describe` is the human-readable symbolic form the WOULD-DO table and pre-commit plan
    rendering show ("row-id", "fingerprint", ...); `extract` is a pure function of that step's
    REAL stdout/content (never called before `of` has really run) that pulls the value out --
    e.g. `tools.setup_tui.runner.parse_row_id` for a `led decision`/`led register-principal` row
    id. `extract` is stored, not baked into a lambda closed over mutable state, so a `Hole` is
    itself immutable/hashable and safely reusable across a plan render.
    """
    of: str
    describe: str
    extract: Callable[[str], str]

    def symbol(self) -> str:
        return f"<{self.describe} of step {self.of!r}>"

    def resolve(self, bindings: "dict[str, str]") -> str:
        """`bindings[self.of]` is the REAL stdout/content `of`'s act produced, populated by the
        commit executor immediately after that act runs -- never before. A hole asked to resolve
        before its binding exists is a commit-executor ordering bug, not a value to guess at, so
        this raises rather than returning a placeholder (ADR-0002: fail loudly, not silently)."""
        if self.of not in bindings:
            raise KeyError(
                f"hole {self.symbol()} asked to resolve before step {self.of!r} has run -- "
                f"a commit-executor ordering defect, not a missing plan entry"
            )
        return self.extract(bindings[self.of])


Arg = Union[str, Hole]


def render_arg(a: Arg) -> str:
    """The symbolic (pre-commit) rendering of one `Arg` -- a plain string renders as itself, a
    `Hole` renders as its symbol. The ONE place this decision is made (ADR-0012 P1) -- every
    act's `render` method below calls this instead of re-deriving the isinstance check."""
    return a.symbol() if isinstance(a, Hole) else a


def resolve_arg(a: Arg, bindings: "dict[str, str]") -> str:
    """The real (commit-time) resolution of one `Arg` -- a plain string resolves to itself
    (nothing to look up), a `Hole` resolves via `Hole.resolve`. Mirrors `render_arg` above."""
    return a.resolve(bindings) if isinstance(a, Hole) else a


# --------------------------------------------------------------------------------------------
# Acts: one dataclass per tools.setup_tui.runner choke point (kept in lockstep by construction --
# the commit executor is the only caller of both an act's `.resolve()` and the choke point it
# feeds).
# --------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class CommandAct:
    """Mirrors `runner.run_command(argv, cwd=, env=, stdin_text=, dry_run=)`.

    PHASE-2 ADDITION -- `extra_env`: several driven verbs (`led register-principal`, `led
    commission`, ...) need `LED_ACTOR=<name>` set alongside the ambient environment (the
    principals_authority.py/signed_genesis.py call sites this act type now serves, moved to the
    commit boundary). A tuple of (key, value) pairs, not a `dict`, so this dataclass stays frozen
    AND hashable by construction (a `dict` field would make `hash()` raise the moment anything
    ever hashed an `Act` -- nothing does today, but there is no reason to introduce the trap).
    `None` (the default, and every Phase-1 call site) means "ambient environment only", matching
    `runner.run_command`'s own `env=None` default exactly."""
    argv: tuple[Arg, ...]
    cwd: str | None = None
    stdin_text: Arg | None = None
    extra_env: tuple[tuple[str, str], ...] | None = None
    # CHECKLIST-SPLIT-SPEC ADDITION (design/FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC.md §3):
    # `best_effort` -- the ONE call site is `commit_executor._daemon_script_entry`'s companion
    # run of `<dest>/start-daemons`, whose OWN documented contract is "one daemon's refusal never
    # blocks a sibling's start" -- a nonzero exit there means "at least one daemon refused",
    # never "this act is a defect the commit should halt on" (the per-daemon refusal is already
    # loud in the script's own captured output; blocking every LATER plan entry -- including the
    # verification sweep itself -- on it would be the opposite of the spec's own "never silence"
    # goal). `_run_entry` reports `ok=True` unconditionally for a `best_effort` `CommandAct`
    # while still carrying the REAL exit code/output in `EntryResult.detail`, never hidden
    # (ADR-0002) -- a typed, reviewed extension (ADR-0000 Rule 1), not a downstream guard around
    # one call site. Defaults to `False`: every existing `CommandAct` call site is unaffected.
    best_effort: bool = False
    # GENESIS-GATE ADDITION (ledger row 1918, the verify-commission hard-stop): several driven
    # verbs report success via EXIT CODE ALONE even when the real success signal is a parsed
    # field of their own stdout (`verify-commission`'s own "TWO VERBS" contract -- it exits 0
    # whether or not its JSON body's `verdict` is VERIFIED; see `signed_genesis.
    # verify_commission_act`'s own docstring). `verdict_check`, if set, is the ONE place
    # `commit_executor._run_entry` learns the REAL ok/detail for such an act, taking priority
    # over the exit-code-based derivation below -- a generic hook (no signed_genesis import
    # here, matching `CallableAct`'s own "kept generic on purpose" discipline), reusable by any
    # future act whose exit code is not its truth. `None` (the default, every prior call site)
    # means "exit code is the truth", byte-identical to every act built before this field
    # existed (ADR-0004 minimal-touch).
    verdict_check: "Callable[[str], tuple[bool, str]] | None" = None

    def render(self) -> str:
        return " ".join(render_arg(a) for a in self.argv)

    def resolve(self, bindings: "dict[str, str]") -> tuple[list[str], str | None]:
        argv = [resolve_arg(a, bindings) for a in self.argv]
        stdin = resolve_arg(self.stdin_text, bindings) if self.stdin_text is not None else None
        return argv, stdin

    def resolve_env(self) -> "dict[str, str] | None":
        """`None` if `extra_env` is unset (the commit executor then passes `env=None` straight
        through to `runner.run_command`, i.e. ambient environment, byte-identical to every
        Phase-1 act); otherwise the ambient environment merged with `extra_env` (later keys win),
        computed fresh at commit time rather than captured at plan-build time -- the same
        "resolved at commit, not at decision" discipline every other `resolve*` method here
        follows."""
        if self.extra_env is None:
            return None
        return {**os.environ, **dict(self.extra_env)}


@dataclass(frozen=True)
class WriteAct:
    """Mirrors `runner.write_file(path, content, dry_run=)`.

    CHECKLIST-SPLIT-SPEC ADDITION (design/FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC.md §3) --
    `executable`: `runner.write_file` preserves an EXISTING target's mode, or falls back to the
    umask-adjusted `open(path, "w")` default (module docstring) -- neither path ever sets the
    executable bit for a file that does not already exist, which is correct for every prior
    call site (a TOML config, CLAUDE.md, an exported key -- none of those are meant to be run)
    but wrong for the one new call site that IS meant to be run directly by the operator
    (`<dest>/start-daemons`, commit_executor.py's own `_daemon_script_entry`). Kept as a typed
    field on the Act itself, not a special case in `commit_executor._run_entry`'s dispatch,
    per ADR-0000 Rule 2(a): "executable-or-not" is a property of the WRITE, the same register
    `write_file`'s own mode-preservation logic already reasons in, not a one-off carve-out for
    a single path string. Defaults to `False` -- every existing call site (TOML/CLAUDE.md/keys/
    checklist saves) is unaffected, byte-for-byte the same behavior as before this field existed
    (ADR-0004 minimal-touch)."""
    path: Arg
    content: Arg
    executable: bool = False

    def render(self) -> str:
        return f"write {render_arg(self.path)}"

    def resolve(self, bindings: "dict[str, str]") -> tuple[str, str]:
        return resolve_arg(self.path, bindings), resolve_arg(self.content, bindings)


@dataclass(frozen=True)
class BackgroundAct:
    """Mirrors `runner.start_background(argv, cwd=, dry_run=)`."""
    argv: tuple[Arg, ...]
    cwd: str | None = None

    def render(self) -> str:
        return " ".join(render_arg(a) for a in self.argv) + "   (background)"

    def resolve(self, bindings: "dict[str, str]") -> list[str]:
        return [resolve_arg(a, bindings) for a in self.argv]


@dataclass(frozen=True)
class CallableAct:
    """FINDING-2 ADDITION (fresh-context review of b565db1): a generic commit-time effect for the
    rare case that is NEITHER of the three runner choke points but must still happen only at
    commit time, never at decision time -- the one instance today is signed_genesis.py's scratch
    GNUPGHOME preparation for `--scripted` witnessing (a real `mkdtemp` + a cleartext-passphrase
    batch-file write), which used to run at decision time, a real filesystem effect outside the
    spec's two declared exceptions and invisible to the §2.8 purity gate.

    `fn` runs with NO arguments at commit time (every decision-time input it needs -- e.g.
    name/email for the scratch keygen -- is already captured in `fn`'s own closure at PLAN-BUILD
    time; only the OUTPUT this act produces is unknown until commit, same as any other act) and
    returns `(ok, detail)` -- `detail` becomes this entry's `produces` binding value (e.g. the
    scratch GNUPGHOME path a later `Hole` depends on, exactly like a `CommandAct`'s real stdout)
    and the `EntryResult`'s own detail. `fn` must never raise for an ordinary "this failed" case
    (return `(False, detail)` instead); an exception propagates as an unanticipated defect, same
    as any other act -- `commit_executor.execute` does not catch it.

    Kept generic on PURPOSE (no signed_genesis import here, or in commit_executor.py): the act
    only knows "call this function, record what it returns" -- the actual scratch-preparation
    logic stays owned by signed_genesis.py, its one home (ADR-0012 P1), not duplicated or
    special-cased into the generic executor."""
    fn: Callable[[], "tuple[bool, str]"]
    label: str

    def render(self) -> str:
        return self.label


Act = Union[CommandAct, WriteAct, BackgroundAct, CallableAct]


# --------------------------------------------------------------------------------------------
# DaemonSelection (design/FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC.md §3): "selected daemons become
# one fact with one home" -- NOT an Act (constructing one performs no effect; it is pure
# accumulated data, legal in the decision phase exactly like a PlanEntry append) and not
# consumed by `commit_executor._run_entry`'s per-Act dispatch. It is read exactly twice, both
# times by `commit_executor.execute` itself: once to derive the generated `<dest>/start-daemons`
# script (a synthesized `WriteAct` entry, §3 point 1), and once, after every ordinary entry has
# committed, to derive the end-of-run verification sweep (§3 point 3).
# --------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class DaemonSelection:
    """One standing service THIS run selected to start (the maintainer's g.1 commission,
    verbatim: "a daemon collection script depending on selected options that start all relevant
    daemons"). Appended to `Plan.daemons` by any screen that selects a standing service --
    today `screen_boundary` (the boundary service) and `screen_observability` (otelcol,
    otel-watch); "anything future" per the spec is a plain append, no new plumbing needed.

    `argv`/`cwd` are plain strings, never `Hole`s: unlike an ordinary `PlanEntry`, a
    `DaemonSelection`'s argv is never resolved against another entry's commit-time output --
    every daemon this build supports is startable from facts already known in the decision
    phase (a chosen port, a resolved interpreter, a destination path), so a `Hole` carrier
    would be machinery with no instance that needs it (ADR-0000: no type without a class it
    forecloses).

    `health_probe` is a closed two-scheme string, never program text spliced anywhere -- the
    ONE vocabulary `commit_executor._probe_daemon` and this module's own `daemon_scaffold`
    module both read: `"http:<url>"` (a GET expected to return an HTTP-level 2xx/3xx; the
    boundary service's `/health`, otelcol's `health_check` extension) or `"pidof:<pattern>"`
    (a `pgrep -f <pattern>` liveness check; otel-watch, which exposes no HTTP endpoint of its
    own). An empty string means "no live-verifiable signal for this daemon" -- honestly
    unrepresentable as either scheme, so the end-of-run sweep records the named absence
    (`checklist.NOT_UP`) rather than fabricating a probe that isn't there (ADR-0002).

    `prerequisite`, if set, is an absolute path the GENERATED SCRIPT checks for (at script RUN
    time, on the operator's own machine, possibly long after this plan was built) before
    starting this one daemon -- e.g. the otelcol binary's resolved path, or `None` if that
    lookup itself failed at selection time (the missing-binary case IS a legitimate
    prerequisite name: "otelcol-contrib (not found on PATH at selection time)", so the refusal
    the script prints on a machine that still lacks it is not a placeholder, it is the fact)."""
    name: str
    argv: tuple[str, ...]
    cwd: str | None
    env_notes: str
    health_probe: str
    prerequisite: str | None = None


# --------------------------------------------------------------------------------------------
# PlanEntry / Plan
# --------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class PlanEntry:
    """One row of THE PLAN -- spec §2.2's four carried facts: the exact act, the checklist name,
    the lesson line, and (for an entry whose real output a later `Hole` depends on) the
    `produces` binding name. `produces` is `None` for the common case (an act nothing later
    needs the output of)."""
    screen: str
    item: str
    lesson: str
    act: Act
    produces: str | None = None


@dataclass
class Plan:
    """THE PLAN: append-only (spec §2.1 -- "the only inter-screen state is the append-only
    plan"), built entirely by the pure decision phase, consumed exactly once by
    `commit_executor.execute`. `daemons` is the sibling accumulation CHECKLIST-SPLIT-SPEC §3
    adds: append-only exactly like `entries`, read by `commit_executor.execute` (never by a
    screen) to derive the generated script and the end-of-run verification sweep."""
    entries: list[PlanEntry] = field(default_factory=list)
    daemons: list[DaemonSelection] = field(default_factory=list)

    def append(self, entry: PlanEntry) -> None:
        self.entries.append(entry)

    def add_daemon(self, selection: DaemonSelection) -> None:
        self.daemons.append(selection)

    def render(self) -> str:
        """The WOULD-DO table (spec §2.3 -- "the dry-run WOULD-DO table promoted from rehearsal
        artifact to the flow's centerpiece"). Every hole renders symbolically; nothing here
        resolves a value or performs an act."""
        lines = [f"{'SCREEN':<20} {'ITEM':<40} ACT"]
        lines.append("-" * 100)
        for e in self.entries:
            lines.append(f"{e.screen:<20} {e.item:<40} {e.act.render()}")
        lines.append("-" * 100)
        lines.append(f"{len(self.entries)} entr{'y' if len(self.entries) == 1 else 'ies'} total")
        return "\n".join(lines)

    def dry_run_rendering(self) -> str:
        """WPC7 (spec §4): a dry run's plan rendering must be byte-identical to a committed run's
        PRE-commit rendering for the same answers -- both are `render()` on the SAME `Plan`, so
        this is `render()` under a different name at the one call site that documents the
        parity claim, not a second implementation that could drift from it."""
        return self.render()
