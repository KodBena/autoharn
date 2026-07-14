# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T22:13:49Z
#   last-change: 2026-07-14T22:13:49Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""act_stream.contract — the VENDOR-NEUTRAL act-stream contract (consult 25 §2.1).

This module is the Python side of the vendor-neutral contract whose DDL is
`claude_harness/db/harness/003_acts_stream.sql`. It contains ZERO vendor-isms — no "session
JSONL", no "subagent", no "workflow journal". Those words live ONLY in a vendor adapter
(`claude_code_adapter.py`), which is vendor-specific by construction and says so. A second
vendor is a second adapter over this same contract.

Design law it obeys:
  - ADR-0000/0012 P8: the typed `Act`/`Stream`/`Manifest` dataclasses ARE the contract; a value
    the annotation forbids never reaches the DB writer.
  - F-D law (consult 25 §2.1): `id` (ingestion order) is THE key; `vendor_seq`/`vendor_ts` are
    metadata that never key. This module never sorts or matches on them.
  - F49 (the ledger_edb idiom): the `Manifest` declares per-family {PRODUCED|CAPABLE|DEFERRED|
    EXCLUDED}; `require()` refuses a family the stream did not PRODUCE, loudly (ADR-0015 Rule 4),
    never a silent empty read as "none exist".
  - Lazy imports banned: every import is top-of-file (stdlib + subprocess psql — the ledger_edb
    idiom, no driver dependency).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pghost_resolve import resolve_pghost  # noqa: E402

PGHOST = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
DB = os.environ.get("HARNESS_DB", "harness")

# The CLOSED, widen-only kind vocabulary (§2.1.1) — the SSOT mirrors act_kind in the DDL; a parity
# check (verify_adapter.py) pins the two, never a silent hand-sync.
KINDS: frozenset[str] = frozenset({
    "tool_call", "tool_result", "delegation_spawn", "delegation_return",
    "plan_item_created", "plan_item_updated", "plan_item_closed", "message_in", "message_out",
})

# The bounded excerpt length (one home, P1 — not a bare literal strewn at call sites).
EXCERPT_MAX = 280


class FamilyStatus(str, Enum):
    """A fact family's guarantee level in a stream's manifest (F49; the ledger_edb capability idiom)."""
    PRODUCED = "produced"    # emitted into this stream
    CAPABLE = "capable"      # the vendor CAN produce it, but this run did not (declared, not silent)
    DEFERRED = "deferred"    # a named guarantee level not reached (e.g. live hook capture — mechanism 2)
    EXCLUDED = "excluded"    # deliberately not an act (model reasoning; token accounting)


@dataclass(frozen=True)
class Manifest:
    """Per-fact-family {status: reason}. A consumer require()s a family and is refused LOUDLY if the
    stream did not PRODUCE it — never a silent empty (F49)."""
    families: dict[str, tuple[FamilyStatus, str]] = field(default_factory=dict)

    def produced(self) -> set[str]:
        return {f for f, (s, _) in self.families.items() if s is FamilyStatus.PRODUCED}

    def require(self, family: str) -> None:
        st = self.families.get(family)
        if st is None or st[0] is not FamilyStatus.PRODUCED:
            reason = st[1] if st else "not a declared family"
            level = st[0].value if st else "absent"
            raise CapabilityError(
                f"stream did not PRODUCE '{family}' ({level}): {reason}. "
                f"A silent empty here would be the F49 vacuous-pass; refusing loudly (ADR-0015 R4).")

    def to_json(self) -> str:
        return json.dumps({f: {"status": s.value, "reason": r}
                           for f, (s, r) in sorted(self.families.items())}, sort_keys=True)


class CapabilityError(RuntimeError):
    """A consumer required a family this stream did not produce (ADR-0015 R4)."""


@dataclass(frozen=True)
class Act:
    """One act, contract-shaped. `id` (ingestion order) is assigned by the DB on INSERT — THE key;
    it is deliberately absent here. `vendor_seq`/`vendor_ts` are metadata that NEVER key."""
    actor: str                         # 'main' | 'sub:<label>' | 'human:<who>' — from record structure
    kind: str                          # a member of KINDS (validated at construction)
    name: str | None = None            # tool name / agent label / plan verb
    target: str | None = None          # path / db object / ledger row ref, when classifiable
    payload_sha256: str = ""           # always set by from_payload; the raw stays in the ephemera
    payload_excerpt: str | None = None
    vendor_seq: str | None = None      # the vendor's own record id — METADATA, never keys
    vendor_ts: str | None = None       # the vendor's wall-clock — METADATA, never keys

    def __post_init__(self) -> None:
        if self.kind not in KINDS:  # illegal states unrepresentable at the boundary (ADR-0000)
            raise ValueError(f"act kind {self.kind!r} not in the closed vocabulary {sorted(KINDS)}")

    @staticmethod
    def sha_excerpt(payload: str) -> tuple[str, str]:
        """The always-present payload hash + the bounded excerpt (P1: one home for both)."""
        h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        ex = payload if len(payload) <= EXCERPT_MAX else payload[:EXCERPT_MAX] + "…"
        return h, ex


@dataclass(frozen=True)
class Stream:
    """One adapter run over one completed source. Its manifest declares what it produced (F49)."""
    run_id: str
    adapter: str
    source_ref: str
    manifest: Manifest
    acts: tuple[Act, ...]


def _psql(sql: str, *, params: dict[str, str] | None = None) -> str:
    """Run one SQL statement against the harness DB via psql (the ledger_edb idiom — no driver
    dependency). Values cross as `:'var'` psql string literals (injection-safe). SQL on STDIN."""
    cmd = ["psql", "-h", PGHOST, "-d", DB, "-tA", "-v", "ON_ERROR_STOP=1"]
    for k, v in (params or {}).items():
        cmd += ["-v", f"{k}={v}"]
    r = subprocess.run(cmd, input=sql, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"psql failed ({r.returncode}): {r.stderr.strip()}")
    return r.stdout.strip()


def persist(stream: Stream, *, schema: str = "acts") -> int:
    """Insert a stream + its acts into the harness acts contract, in ingestion order (id-is-order).
    Returns the stream id. The acts table is append-only (the DDL trigger); this is the ONE write
    path. Raises loudly on any failure (ADR-0002) — never a partial silent insert."""
    # Wrap RETURNING in a CTE+SELECT so -tA prints only the id (a bare INSERT..RETURNING also
    # prints the "INSERT 0 1" command tag; the SELECT form is clean — the file_rationalization idiom).
    sid = int(_psql(
        f'WITH ins AS (INSERT INTO "{schema}".stream (run_id, adapter, source_ref, manifest) '
        f"VALUES (:'run', :'adapter', :'src', :'manifest'::jsonb) RETURNING id) SELECT id FROM ins;",
        params={"run": stream.run_id, "adapter": stream.adapter, "src": stream.source_ref,
                "manifest": stream.manifest.to_json()}))
    for a in stream.acts:  # ingestion order == emission order == the id sequence
        _psql(
            f'INSERT INTO "{schema}".act '
            "(run_id, stream_id, vendor_seq, vendor_ts, actor, kind, name, target, "
            " payload_sha256, payload_excerpt) VALUES "
            "(:'run', :sid, NULLIF(:'vseq',''), NULLIF(:'vts','')::timestamptz, :'actor', :'kind', "
            " NULLIF(:'name',''), NULLIF(:'target',''), :'sha', NULLIF(:'excerpt',''));",
            params={"run": stream.run_id, "sid": str(sid), "vseq": a.vendor_seq or "",
                    "vts": a.vendor_ts or "", "actor": a.actor, "kind": a.kind, "name": a.name or "",
                    "target": a.target or "", "sha": a.payload_sha256, "excerpt": a.payload_excerpt or ""})
    return sid
