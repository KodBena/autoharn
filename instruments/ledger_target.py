# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T10:06:34Z
#   last-change: 2026-07-18T11:07:10Z
#   contributors: be693afb/main, a857c93d/main, ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""SSOT for WHERE a ledger lives and HOW its actor model works — the single source every
instrument resolves its (host, database, schema, subject-actor predicate) from.

ADR-0000 Rule 2(a): the class this type forecloses is "an instrument silently targets the
wrong place, or crashes on an apparatus object that its target does not carry." Before this
SSOT each instrument re-derived the target from scattered constants — `PGDB = "epistemic"`
hardcoded here, `PGLEDGERDB` env there, `rel = f"{session}.ledger"` using the session arg as
the schema name — and some hardcoded `kernel.principal`, which lives ONLY in `epistemic`. When
the subject ledger moved to the isolated database `nla` (schema `public`, actor a text column,
NO `kernel.principal`), two mandatory close instruments crashed and one produced silence read
as clean (link 21's F49). The scattered target-resolution is the representable class; a single
resolved `LedgerTarget` is the type that closes it.

Closure statement (ADR-0000 2026-07-02 amendment):
  - invariant: every ledger-querying instrument resolves (db, schema, actor-model) from THIS
    module, by target NAME, and refuses/degrades LOUDLY (ADR-0015 Rule 4) on a capability its
    target lacks — never a silent crash, never a wrong-place query.
  - quantification universe: axes = {database, schema, subject-actor model, presence of an
    apparatus relation, the CONSUMER substrate pointers (fenced work-dir + subject session dir —
    added for finding 36: these are per-target facts too, and a module-global default for them is the
    same wrong-place-query class as a hardcoded db)}; siblings = every instrument that opens a psql
    connection to a ledger OR resolves a per-run substrate path from a target name (soundness,
    close_sweep, observed_currency, contemporaneity, stale_enactment_debt, close_manifest's acts/perf
    consumers, and the historical-replay set gains it on touch, ADR-0004).
  - denomination: the target is resolved from the run's declared target NAME, never a proxy
    (a bare schema string that is ambiguous between `epistemic.public` and `nla.public`).

TARGET RESOLUTION (db, schema, kern) now derives from the ONE home `engine/targets.py`
(design/ORCH-USE-MODE-ENGINE-WIRING.md item 1; ADR-0012 P1) — the same home `engine/ledger_edb.py`
derives from, so the two are never hand-synced duplicate copies (the db/schema agreement with
`engine/ledger_edb.py` is pinned by engine/tests/test_ledger_marriage.py ::
test_target_parity_against_operator_ssot, run by subprocess against a fresh interpreter that only
has THIS directory on sys.path — this module reaches `engine/targets.py` itself, by its own
file-relative sys.path insert, so that subprocess needs no help finding it). What stays local to
THIS module: the INSTRUMENT-only per-target fields (`subject_actor_sql`, `subject_role`,
`fenced_dir`, `subject_session_dir`) that `engine/targets.py`'s `TargetInfo` does not carry — those
are this SSOT's own domain, not the engine's.

`_KERNEL_SUBJECT`'s schema literal is now PARAMETERIZED from the target's `kern` (the sibling of
finding 51 named in design/ORCH-USE-MODE-ENGINE-WIRING.md: this literal used to hardcode `kernel.principal`
regardless of a target's actual kernel schema). The `name='subject'` half is UNCHANGED — finding 51's
own scope (the principal-actor assumption), explicitly not touched or regressed here.
"""
import os
import subprocess
import sys
from dataclasses import dataclass

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)  # autoharn root
sys.path.insert(0, os.path.join(_REPO_ROOT, "engine"))

import targets  # noqa: E402  (engine/targets.py, the ONE home for (db, schema, kern) resolution)
from pghost_resolve import resolve_pghost  # noqa: E402

PGHOST = resolve_pghost("EPISTEMIC_PGHOST")
FS, RS = "\x1f", "\x1e"


def _kernel_subject_sql(kern: str) -> str:
    """The subject-actor predicate for a kernel-shape lineage: the actor column holds a
    `{kern}.principal` id, and the subject is the row named 'subject'. Only the SCHEMA half of
    this literal is parameterized (from the target's own `kern`, engine/targets.py); the
    `name='subject'` half is finding 51's own scope and is deliberately NOT touched here."""
    return f"(SELECT id FROM {kern}.principal WHERE name='subject')"


@dataclass(frozen=True)
class LedgerTarget:
    """Where a ledger lives and how to name its subject actor. Resolved by name via `resolve`."""
    name: str
    db: str
    schema: str
    kern: str = "kernel"  # this target's KERNEL schema (engine/targets.py); "kernel" for the
    # historical apparatus lineage, "toycolors_kernel" for toy -- never a literal at a call site.
    # A SQL scalar expression equal to the subject's `actor` value on THIS target. On the
    # isolated `nla` ledger the actor is the text role that wrote the row; on the kernel lineage
    # it is a principal id. An instrument that filters "authored by the subject" uses this, so it
    # never assumes an actor model its target does not have. `resolve()` always populates this
    # explicitly (the kernel-shape default is `_kernel_subject_sql(self.kern)`, never a class-level
    # literal, so it varies correctly per target).
    subject_actor_sql: str = ""
    # The DB LOGIN role the subject connects as — the `role=` token in the off-host tee.log for
    # this target's subject writes. `None` derives it as `led_{schema}` (the historical lineage
    # convention); `nla` overrides it to the isolated role. An instrument scanning the tee.log for
    # the subject's lines uses `login_role`, never a hardcoded `led_{session}` that misses `nla`.
    subject_role: str | None = None
    # The fenced WORK directory the subject wrote under — the acts consumers' `--fenced` prefix
    # (acts_join.py classifies a ledger row as a CLAIM iff its evidence starts with this path, and an
    # act as RELEVANT iff it writes under it). Target-resolved here, NOT a close_manifest module-global
    # default: before this field a bare `close_manifest.py e16` read e15's fenced default (`~/nk4-build`)
    # against e16's ledger and silently EMPTIED every acts consumer (finding 36 — the exact F49
    # wrong-substrate vacuous pass the ledger_target SSOT was built to foreclose, here on the substrate
    # POINTER instead of the db/schema). `None` = this target carries no fenced substrate; a
    # consumer-bearing target with `None` here renders its acts lines REQUIRED-ABSENT (RED) at close,
    # never silently empty. `~` is expanded at the point of use.
    fenced_dir: str | None = None
    # The subject SESSION-transcript dir — the row_performed_by consumer's `--session-dir` (the full
    # ledger-INSERT act commands live in the transcript, not the truncated acts contract). Same
    # target-resolution discipline and same finding-36 defect as `fenced_dir`: reading e15's transcript
    # against e16's rows left every row unbound (`unbound_row(1..7)`, run B's specimen). `None` = no
    # session substrate registered for this target (→ REQUIRED-ABSENT at close for a perf consumer).
    subject_session_dir: str | None = None

    @property
    def login_role(self) -> str:
        return self.subject_role or f"led_{self.schema}"

    def rel(self, table: str = "ledger") -> str:
        return f"{self.schema}.{table}"

    def run(self, sql: str, *, check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["psql", "-h", PGHOST, "-d", self.db, "-tA", "-F", FS, "-R", RS, "-c", sql],
            capture_output=True, text=True, check=check)

    def scalar(self, sql: str) -> str:
        return self.run(sql).stdout.strip()

    def rows(self, sql: str) -> list[list[str]]:
        out = self.run(sql).stdout
        return [r.split(FS) for r in out.rstrip("\n").split(RS) if r.strip()]

    def has_relation(self, qualified: str) -> bool:
        """True iff a schema-qualified relation (e.g. 'kernel.principal') exists on this target.
        The capability check that lets an instrument degrade LOUDLY instead of crashing."""
        return self.scalar(f"SELECT to_regclass('{qualified}') IS NOT NULL;") == "t"

    def has_col(self, col: str, table: str = "ledger") -> bool:
        return self.scalar(
            f"SELECT 1 FROM information_schema.columns WHERE table_schema='{self.schema}' "
            f"AND table_name='{table}' AND column_name='{col}';") == "1"


@dataclass(frozen=True)
class _Extras:
    """The INSTRUMENT-only per-target fields `engine/targets.py`'s `TargetInfo` does not carry —
    this SSOT's own domain (the subject's actor model + the finding-36 substrate pointers). `None`/
    unset fields fall back to the kernel-shape defaults in `resolve()` (never a silent module-global,
    per the closure statement above)."""
    subject_actor_sql: str | None = None
    subject_role: str | None = None
    fenced_dir: str | None = None
    subject_session_dir: str | None = None


# Per-target INSTRUMENT extras (subject actor model + substrate pointers) -- db/schema/kern dissolved
# into `engine/targets.py` (the ONE home, ADR-0012 P1); a name absent here simply carries no extras
# (the kernel-shape subject_actor_sql default, no registered substrate -- REQUIRED-ABSENT at close,
# never a silent empty, finding 36).
_INSTRUMENT_EXTRAS: dict[str, _Extras] = {
    # the live, isolated subject ledger (e14+): a single text-role actor (the subject connects and
    # writes as `nla_rw`); no kernel.principal here.
    "nla": _Extras(subject_actor_sql="'nla_rw'", subject_role="nla_rw"),
    # e15: the s15 subject kernel (consult 25 §2.3 / A.3). Unlike nla, s15 IS kernel-shape
    # (kernel.principal + regards present — the directive commissions countersigning). The subject
    # principal is the generic seeded 'author' (NO workflow agents are pre-created — measurement (d)).
    "e15": _Extras(subject_actor_sql="(SELECT id FROM kernel.principal WHERE name='author')",
                   subject_role="vsr_rw",
                   # e15's consumer substrate (oracle §7 concretization): the nk4 fenced dir the
                   # subject wrote under + the persisted e15 subject session transcript. These were
                   # close_manifest.py's hardcoded module-global defaults (ACTS_FENCED / PERF_SESSION_DIR)
                   # before finding 36 — read them here as the target-resolved SSOT, not there.
                   fenced_dir="~/nk4-build",
                   subject_session_dir="~/w/vdc/1/claude_harness/docs/claude-ephemera/"
                   "session-b3644a33-e15-subject/-home-bork-nk4-build"),
    # e16: the s16 subject kernel (s15 byte-identical — no vocabulary change, consult 29 §3). One
    # lever: the F50 no-license branch.
    "e16": _Extras(subject_actor_sql="(SELECT id FROM kernel.principal WHERE name='author')",
                   subject_role="hvn_rw",
                   # e16's consumer substrate (label zc9): the fenced dir e16's row 6/act 368 live
                   # under + the e16 subject session transcript. A bare e16 close now reads THESE,
                   # not e15's — closing finding 36. (RCA close-substrate-rca-2026-07-07.md proved
                   # the delta line-by-line: with these, run A's readings reproduce.)
                   fenced_dir="~/zc9-build",
                   subject_session_dir="~/w/vdc/1/claude_harness/docs/claude-ephemera/"
                   "session-5ffc3bed-e16-subject/-home-bork-zc9-build"),
    # e17: the s17 subject kernel (s15 + interception stamps + independence vocabulary; Inc8/9). One
    # lever: refuse-and-teach at the independence seam (F53, acts.ruling id 29). subject_session_dir
    # is filled at ARM/analysis (the subject session id is unknown pre-run) — the finding-36 gate
    # correctly REDs a bare e17 close until it is registered (consult 33 §5a).
    "e17": _Extras(subject_actor_sql="(SELECT id FROM kernel.principal WHERE name='author')",
                   subject_role="wmb_rw",
                   fenced_dir="~/kt3-build",
                   # the completed run's persisted subject session (Inc10 capture) — the project-slug
                   # dir carrying session-transcript/ + subagents/ (incl. the reviewer a8d15e15).
                   subject_session_dir="~/w/vdc/1/claude_harness/docs/claude-ephemera/"
                   "session-38484b24-e17-subject/-home-bork-kt3-build"),
    # e18: the s18 subject kernel (s18 = s17 BYTE-IDENTICAL, Addendum A — no write-time change; the
    # finding-38 class is covered by the descriptive review_without_detail line, not a kernel delta).
    # One lever: is a delta-attest a fixed point (review_fixpoint, K=2 fresh criterion reviews;
    # consult 37).
    "e18": _Extras(subject_actor_sql="(SELECT id FROM kernel.principal WHERE name='author')",
                   subject_role="qbx_rw",
                   fenced_dir="~/jm7-build",
                   # the completed run's persisted subject session (session 9c467b69, run 2026-07-07):
                   # transcript + the reviewer subagent a98d8fc5b34db3036 (ledger entry 8's stamp).
                   subject_session_dir="~/w/vdc/1/claude_harness/docs/claude-ephemera/"
                   "session-9c467b69-e18-subject/-home-bork-jm7-build"),
}


def resolve(name: str) -> LedgerTarget:
    """Resolve a target NAME to its LedgerTarget. (db, schema, kern) derive from `engine/targets.py`
    (the ONE home; raises loudly there on an unrecognized name, ADR-0002 — never a silent wrong-db
    fallthrough). The instrument-only extras (subject actor model, substrate pointers) come from
    THIS module's own registry, defaulting to the kernel-shape subject predicate (parameterized by
    the target's `kern`) and no registered substrate where a name carries no extras."""
    if os.environ.get("LEDGER_DB") or os.environ.get("LEDGER_SCHEMA") or os.environ.get("LEDGER_KERN"):
        db = os.environ.get("LEDGER_DB", "epistemic")
        schema = os.environ.get("LEDGER_SCHEMA", name)
        kern = os.environ.get("LEDGER_KERN", "kernel")
        actor = "'nla_rw'" if db == "nla" else _kernel_subject_sql(kern)
        return LedgerTarget(name, db=db, schema=schema, kern=kern, subject_actor_sql=actor)
    ti = targets.resolve(name)  # raises ValueError on an unrecognized name -- see engine/targets.py
    extra = _INSTRUMENT_EXTRAS.get(name, _Extras())
    return LedgerTarget(
        name, db=ti.db, schema=ti.schema, kern=ti.kern,
        subject_actor_sql=extra.subject_actor_sql or _kernel_subject_sql(ti.kern),
        subject_role=extra.subject_role, fenced_dir=extra.fenced_dir,
        subject_session_dir=extra.subject_session_dir)
