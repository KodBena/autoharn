# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T19:33:00Z
#   last-change: 2026-07-19T19:48:18Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

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
    """Mirrors `runner.write_file(path, content, dry_run=)`."""
    path: Arg
    content: Arg

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
    `commit_executor.execute`."""
    entries: list[PlanEntry] = field(default_factory=list)

    def append(self, entry: PlanEntry) -> None:
        self.entries.append(entry)

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
