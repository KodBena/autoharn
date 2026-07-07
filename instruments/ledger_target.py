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
"""
import os
import subprocess
from dataclasses import dataclass

PGHOST = os.environ.get("EPISTEMIC_PGHOST", "192.168.122.1")
FS, RS = "\x1f", "\x1e"

# The subject-actor predicate for the kernel-era lineage (s13+ in `epistemic`): the actor column
# holds a kernel.principal id, and the subject is the row named 'subject'.
_KERNEL_SUBJECT = "(SELECT id FROM kernel.principal WHERE name='subject')"


@dataclass(frozen=True)
class LedgerTarget:
    """Where a ledger lives and how to name its subject actor. Resolved by name via `resolve`."""
    name: str
    db: str
    schema: str
    # A SQL scalar expression equal to the subject's `actor` value on THIS target. On the
    # isolated `nla` ledger the actor is the text role that wrote the row; on the kernel lineage
    # it is a principal id. An instrument that filters "authored by the subject" uses this, so it
    # never assumes an actor model its target does not have.
    subject_actor_sql: str = _KERNEL_SUBJECT
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


# The ONE home mapping a target NAME to where it lives. Special targets are explicit; any other
# name is derived as a schema in the historical apparatus database (`epistemic`) — the closed-
# evidence per-session lineages s6..s13 — so the registry is not a stale enumeration (ADR-0012 P1).
_SPECIAL: dict[str, LedgerTarget] = {
    # the live, isolated subject ledger (e14+): its own database, schema `public`, a single
    # text-role actor (the subject connects and writes as `nla_rw`); no kernel.principal here.
    "nla": LedgerTarget("nla", db="nla", schema="public", subject_actor_sql="'nla_rw'",
                        subject_role="nla_rw"),
    # e15: the s15 subject kernel in the FRESH ISOLATED opaque db `vsr` (consult 25 §2.3 / A.3).
    # Unlike nla, s15 IS kernel-shape (kernel.principal + regards present — the directive commissions
    # countersigning). The subject principal is the generic seeded 'author' (NO workflow agents are
    # pre-created — measurement (d)). `e15` is the OPERATOR target name only; the subject-facing db/
    # schema/role are the opaque `vsr`/`public`/`vsr_rw` (the s15 name appears in no subject byte).
    "e15": LedgerTarget("e15", db="vsr", schema="public", subject_role="vsr_rw",
                        subject_actor_sql="(SELECT id FROM kernel.principal WHERE name='author')",
                        # e15's consumer substrate (oracle §7 concretization): the nk4 fenced dir the
                        # subject wrote under + the persisted e15 subject session transcript. These were
                        # close_manifest.py's hardcoded module-global defaults (ACTS_FENCED / PERF_SESSION_DIR)
                        # before finding 36 — read them here as the target-resolved SSOT, not there.
                        fenced_dir="~/nk4-build",
                        subject_session_dir="~/w/vdc/1/claude_harness/docs/claude-ephemera/"
                        "session-b3644a33-e15-subject/-home-bork-nk4-build"),
    # e16: the s16 subject kernel (s15 byte-identical — no vocabulary change, consult 29 §3) in the FRESH
    # ISOLATED opaque db `hvn` (label `zc9`, role `hvn_rw`; M4). One lever: the F50 no-license branch.
    "e16": LedgerTarget("e16", db="hvn", schema="public", subject_role="hvn_rw",
                        subject_actor_sql="(SELECT id FROM kernel.principal WHERE name='author')",
                        # e16's consumer substrate (label zc9): the fenced dir e16's row 6/act 368 live
                        # under + the e16 subject session transcript. A bare e16 close now reads THESE,
                        # not e15's — closing finding 36. (RCA close-substrate-rca-2026-07-07.md proved
                        # the delta line-by-line: with these, run A's readings reproduce.)
                        fenced_dir="/home/bork/zc9-build",
                        subject_session_dir="/home/bork/w/vdc/1/claude_harness/docs/claude-ephemera/"
                        "session-5ffc3bed-e16-subject/-home-bork-zc9-build"),
    # e17: the s17 subject kernel (s15 + interception stamps + independence vocabulary; Inc8/9) in the
    # FRESH ISOLATED opaque db `wmb` (label `kt3`, role `wmb_rw`; M4). One lever: refuse-and-teach at the
    # independence seam (F53, acts.ruling id 29). The fenced dir is ~/kt3-build; subject_session_dir is
    # filled at ARM/analysis (the subject session id is unknown pre-run) — the finding-36 gate correctly
    # REDs a bare e17 close until it is registered (consult 33 §5a).
    "e17": LedgerTarget("e17", db="wmb", schema="public", subject_role="wmb_rw",
                        subject_actor_sql="(SELECT id FROM kernel.principal WHERE name='author')",
                        fenced_dir="/home/bork/kt3-build",
                        # the completed run's persisted subject session (Inc10 capture) — the project-slug
                        # dir carrying session-transcript/ + subagents/ (incl. the reviewer a8d15e15).
                        subject_session_dir="/home/bork/w/vdc/1/claude_harness/docs/claude-ephemera/"
                        "session-38484b24-e17-subject/-home-bork-kt3-build"),
    # e18: the s18 subject kernel (s18 = s17 BYTE-IDENTICAL, Addendum A — no write-time change; the
    # finding-38 class is covered by the descriptive review_without_detail line, not a kernel delta) in the
    # FRESH ISOLATED opaque db `qbx` (label `jm7`, role `qbx_rw`; reviewer roles qbx_rev1/qbx_rev2; M4).
    # One lever: is a delta-attest a fixed point (review_fixpoint, K=2 fresh criterion reviews; consult 37).
    "e18": LedgerTarget("e18", db="qbx", schema="public", subject_role="qbx_rw",
                        subject_actor_sql="(SELECT id FROM kernel.principal WHERE name='author')",
                        fenced_dir="/home/bork/jm7-build",
                        # the completed run's persisted subject session (session 9c467b69, run 2026-07-07):
                        # transcript + the reviewer subagent a98d8fc5b34db3036 (ledger entry 8's stamp).
                        subject_session_dir="/home/bork/w/vdc/1/claude_harness/docs/claude-ephemera/"
                        "session-9c467b69-e18-subject/-home-bork-jm7-build"),
}


def resolve(name: str) -> LedgerTarget:
    """Resolve a target NAME to its LedgerTarget. Env `LEDGER_DB`/`LEDGER_SCHEMA` fully override
    for a one-off target (e.g. a scratch mirror). A non-special name is a schema in `epistemic`."""
    if os.environ.get("LEDGER_DB") or os.environ.get("LEDGER_SCHEMA"):
        db = os.environ.get("LEDGER_DB", "epistemic")
        schema = os.environ.get("LEDGER_SCHEMA", name)
        actor = "'nla_rw'" if db == "nla" else _KERNEL_SUBJECT
        return LedgerTarget(name, db=db, schema=schema, subject_actor_sql=actor)
    if name in _SPECIAL:
        return _SPECIAL[name]
    return LedgerTarget(name, db="epistemic", schema=name)
