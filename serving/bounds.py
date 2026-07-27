#!/usr/bin/env python3
"""bounds -- the ONE home (ADR-0012 P1: single source of truth / derive-don't-duplicate) for the
SERVICE layer's bound vocabulary: every named byte-size ceiling boundary_service.py (and any
sibling consumer) enforces.

Motivation (ledger row 1514 item 2, maintainer-ratified 2026-07-27, "the ratified-but-not-yet-
built all should go in"): before this module existed, the 256-byte identity-header bound and the
1 MiB write-body bound each lived as an INDEPENDENT literal -- s65's kernel CHECK said 256,
boundary_service.py's own `IDENTITY_HEADER_MAX_BYTES` said 256, independently; s51's kernel
`artifact_too_large` RAISE said 1 MiB, boundary_service.py's own `MAX_WRITE_BODY_BYTES` said 1
MiB, independently too -- and nothing detected drift between either pair. This module is the
single SERVICE-side home for the whole bound vocabulary; gates/bounds_kernel_drift.py is the
cross-layer mechanism that reads the kernel SQL text directly (never re-typing the kernel's own
number) and asserts each named bound below that has a kernel twin still agrees with it, so an
edit to either side alone -- kernel or service -- goes red.

Every constant below is a PURE RELOCATION out of serving/boundary_service.py (the A2.2/A5.2/A8/
A11 build, plus design/FABLE-DISPATCH-MECHANICS-SPEC.md §1 and design/FABLE-LEGACY-LED-
RETIREMENT-SPEC.md Part B) -- no value changed, no behavior changed anywhere; every response byte
this service was already producing is byte-identical after this move. Each docstring states WHAT
the bound protects and, when one exists, WHERE its kernel-side twin lives (file + CHECK
constraint / object name); a bound with no kernel-side fact (a pure transport wall) says so
explicitly rather than leaving the absence to be inferred.

Consumers (boundary_service.py today; boundary_cli_client.py/boundary_models.py reference these
names only in prose, carrying no private numeric copy of their own) import the names they need
from this module -- never re-declare a private copy. Top-of-file import only (CLAUDE.md: lazy
imports are banned)."""
from __future__ import annotations

# ------------------------------------------------------------------------------------------------
# IDENTITY CONDUIT (design/FABLE-DISPATCH-MECHANICS-SPEC.md §1; the s65 house precedent, design/
# FABLE-S65-REFUSAL-ATTEMPTED-KIND-SPEC.md).
# ------------------------------------------------------------------------------------------------

IDENTITY_HEADER_MAX_BYTES = 256
"""Caps every identity-conduit HTTP header value (both the vendor-stamp headers and the minted-
principal header) in bytes -- refused, never truncated, BEFORE any kernel call.
Kernel twin: kernel/lineage/s65-refusal-attempted-kind.sql, CHECK CONSTRAINT
`refusal_attempted_kind_length` (`octet_length(refusal_attempted_kind) <= 256`) -- the same
256-byte bound, the same "hostile-input backstop for a short token, not a tight fit" rationale,
one layer down. Cross-layer drift between this constant and that CHECK is asserted by
gates/bounds_kernel_drift.py."""

# ------------------------------------------------------------------------------------------------
# WRITE-PATH SIZE AXIS (A2.2/A8; design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md).
# ------------------------------------------------------------------------------------------------

MAX_WRITE_BODY_BYTES = 1_048_576
"""Caps the raw request body, in bytes, BEFORE any JSON parsing, for the four generic
`/write/{surface}` routes (checkpoint (a)) -- generous for any ledger payload; the rationale is
BUFFERING, never hold an unbounded request body in memory.
Kernel twin: kernel/lineage/s51-artifact-store.sql, CHECK CONSTRAINT `artifact_size_within_cap`
(`size <= 1048576`) and the same-valued `artifact_too_large` RAISE inside `kernel.artifact_write`
-- the SAME 1 MiB order of magnitude by shared design rationale (KB-scale payloads: charters/
TOMLs/specs are roughly 100x smaller), though this constant bounds a DIFFERENT surface (the
generic write routes' own buffering wall) than the dedicated artifact route's own bound below.
Cross-layer drift between this constant and that CHECK is asserted by
gates/bounds_kernel_drift.py."""

MAX_PSQL_ARG_BYTES = 100_000
"""Caps the re-serialized write payload, in bytes, as it crosses to postgres as ONE psql
`-v payload=...` argument (checkpoint (b)) -- sized against Linux's PER-ARGUMENT wall,
`MAX_ARG_STRLEN` (32 pages = 131 072 bytes), not the 2 MiB total-argv `ARG_MAX` the pre-A8 bound
was sized against.
No kernel-side twin -- this is a pure TRANSPORT wall (the psql subprocess argv), not a fact the
kernel's own schema encodes anywhere."""

MAX_AFTER_SLUG_BYTES = 512
"""Caps `/work/items`' `after_slug` cursor query parameter, in bytes (A11 item 1) -- `work_slug`
is operator-authored identifier text, not free prose, so 512 is generous headroom, not a measured
ceiling.
No kernel-side twin."""

# ------------------------------------------------------------------------------------------------
# ARTIFACT ROUTE (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part B) -- its own dedicated bound,
# DERIVED from the kernel's artifact-size cap rather than chosen independently.
# ------------------------------------------------------------------------------------------------

_ARTIFACT_KERNEL_CAP_BYTES = 1_048_576
"""`kernel.artifact_write`'s own 1 MiB cap, mirrored here ONLY to DERIVE `MAX_ARTIFACT_BODY_BYTES`
below (never chosen independently of it).
Kernel twin: kernel/lineage/s51-artifact-store.sql, CHECK CONSTRAINT `artifact_size_within_cap`
(`size <= 1048576`) -- the SAME kernel constraint `MAX_WRITE_BODY_BYTES` above cites (one kernel
cap, two service-side derived views: the generic-route buffering wall above, and this dedicated
artifact-route base below). Cross-layer drift between this constant and that CHECK is asserted by
gates/bounds_kernel_drift.py."""

MAX_ARTIFACT_BODY_BYTES = ((_ARTIFACT_KERNEL_CAP_BYTES + 2) // 3) * 4 + 4096
"""Caps `POST /artifacts`' own raw request-body buffering -- DERIVED from
`_ARTIFACT_KERNEL_CAP_BYTES` via the strict base64 inflation ceiling (`ceil(n/3)*4`), never chosen
independently: a payload whose decoded `bytes` field is <= the kernel's own cap can never
re-encode past this bound, so this bound can never disagree with the kernel's own refusal -- it
only bounds how much this service buffers in memory before that refusal is reached. `+4096` is
generous JSON-envelope headroom (`media_type`/`hash`/`actor` keys, quoting), not itself a second
artifact-size judgment.
No independent kernel-side twin of its own -- it is a service-only DERIVED view of
`_ARTIFACT_KERNEL_CAP_BYTES`'s kernel twin, so it is not separately checked by
gates/bounds_kernel_drift.py (checking `_ARTIFACT_KERNEL_CAP_BYTES` against the kernel already
covers it: this constant's own derivation from that one is pure arithmetic, not a second fact)."""
