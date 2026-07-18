#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T07:44:41Z
#   last-change: 2026-07-18T15:35:31Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""boundary_service -- the FastAPI outer boundary Port into an autoharn-managed ledger
(design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md, the RATIFIED build basis; ledger rows 1471,
1481, 1518; orchlog.d/panel-single-boundary-direction.md; kernel/lineage/
s43-typed-verdict-write-boundary.sql; law/adr/0002, 0012 P2, 0016).

WHAT THIS SERVICE IS (spec §0). The kernel's OWN inner boundary -- s43's four SECURITY
DEFINER write functions plus the derived views -- remains the sole authority. This service is
the OUTER declared boundary: it translates and validates, refuses what it cannot honor, and
adds NO truth of its own (ADR-0012 P2, verbatim). Every byte it serves originates in a kernel
view; every byte it writes passes through an s43 boundary function (spec §9's closure
invariant). It never issues a raw INSERT/UPDATE/DELETE against any kernel-governed table --
grep this file for 'INSERT INTO'/'UPDATE '/'DELETE FROM' targeting a table (not a boundary
FUNCTION CALL) and find nothing; W3's witness proves it live on a pre-s43 world too.

TRANSPORT (a choice this spec left open -- FLAGGED as a spec defect in the build report; the
smallest honest resolution taken here): this repository's own filing/ modules (see
filing/record_reading.py's own docstring, point 1) deliberately use a `psql` SUBPROCESS
transport with `-v name=value` / `:'var'` injection-safe substitution, NOT a Python DB driver,
because "this repo has no psycopg dependency" and "the house style" is already established.
This service follows that same house convention rather than introducing a second transport
the project does not otherwise use for its ledger connections -- `led`/`judge`/every filing/
module all connect this same way. Every value interpolated into a SQL string below is either
(a) an integer FastAPI itself already type-validated (a non-integer path/query value is a
422 before this module sees it -- never hand-parsed here), or (b) a deployment-config
identifier (schema/kern/role) validated ONCE at process start against a strict identifier
regex (`_IDENT_RE` below) and refused loudly if it fails -- so no HTTP-controlled string ever
reaches a SQL string via concatenation. Payload BODIES cross as psql `-v payload=...` bind
values (`:'payload'::jsonb`), never spliced as text -- the same idiom kernel_write() in
bootstrap/templates/led.tmpl already uses.

CAPABILITY DETECTION (spec §3 GET /health note: "capability facts are DETECTED per request
start-up, never assumed"). Detection is OBJECT EXISTENCE (`to_regclass`), never a version
literal -- the same migrate-detect-drift discipline led.tmpl's own s43/s45 probes already use
(a world need not match this service's authoring commit exactly). No caching anywhere in this
module (spec §5): every request re-detects, re-reads, re-writes through the kernel fresh.

BIND GUARD (spec §2): refuse to bind any non-loopback address without
--i-understand-this-exposes-the-ledger, construction-time (before uvicorn ever binds a
socket) -- ADR-0002 rung 1, the strongest rung, because the anomaly never reaches a running
server. The spec's own words name '0.0.0.0'; this build refuses EVERY non-loopback host under
the same flag (127.0.0.1/localhost/::1 are the only unguarded binds) -- a specific LAN IP is
exactly as exposing as the wildcard address, and gating on the literal string '0.0.0.0' only
would leave that hazard in reach of the same work untouched (CLAUDE.md's engineering-
responsibility rule). FLAGGED as a deliberate broadening of the spec's literal text, in its
spirit.

NO META-ROUTES (spec A2.1): `docs_url`/`redoc_url`/`openapi_url` are all `None` below --
FastAPI's default `/docs`, `/redoc`, `/openapi.json`, `/docs/oauth2-redirect` are DISABLED, not
merely unenumerated. §9's closure statement's route claim was found false against the running
service (A2.1's HIGH finding: those meta-routes were live, unenumerated, and `/docs`/`/redoc`
pulled a third-party CDN asset) -- a ledger boundary needs no self-documentation surface with
an external dependency; §3/§4 + this file's own docstring + serving/README.md are the
documentation. The route witness (seen-red/boundary-service/run_fixtures.py's W12) asserts
against `app.routes` directly, in-process, never the OpenAPI schema's self-report (which is
now absent entirely and structurally could never have enumerated a meta-route anyway).

SIZE AXIS (spec A2.2, RE-DENOMINATED per A8 item 1): TWO named bounds, one per checkpoint,
because the two checkpoints guard two DIFFERENT walls -- (a) `MAX_WRITE_BODY_BYTES =
1_048_576` (1 MiB) on the raw request body, before any JSON parsing (`_read_bounded_body`:
Content-Length when the client declared one, refused without ever reading the body; the
actual byte count otherwise, refused mid-stream, never buffered whole) -- this bound's
rationale is BUFFERING (never hold an unbounded body in memory); (b) `MAX_PSQL_ARG_BYTES =
100_000` on the re-serialized payload, before the psql subprocess -- this bound's rationale
is TRANSPORT: the payload travels as ONE psql `-v` argument, and Linux's per-argument limit
is `MAX_ARG_STRLEN` (32 pages, 131 072 bytes), NOT the 2 MiB total-argv `ARG_MAX` A2.2
originally sized against; a payload between ~131 KiB and 1 MiB passed both pre-A8
checkpoints and detonated in `subprocess.run` as an uncaught E2BIG `OSError` (bare 500, the
untyped shape §9 forbids). A payload can pass checkpoint (a) and still fail (b) -- any raw
body between the two bounds, or non-ASCII content that `json.dumps`'s default
`ensure_ascii=True` escaping expands past its raw UTF-8 byte count (W9/W25 exercise both).
Both checkpoints return the same typed `payload_too_large` shape (413), whose `limit_bytes`
field is HONEST about which bound fired (A8: never reporting one bound's number for the
other's refusal).

INFRA FAILURE (spec A2.4, narrowed per A3.2): a psql infrastructure failure (unreachable world,
connection refusal, a nonzero exit that is not a kernel verdict, or a `PSQL_EXEC_TIMEOUT_S`
stall) is the ONE thing `_query_json` raises. As of A3 that ONE thing is a DEDICATED exception
class, `PsqlInfraFailure` (never a bare `RuntimeError`) -- so the FastAPI app's single exception
handler catches ONLY `PsqlInfraFailure`, and no foreign exception (a `RecursionError` that
happens to subclass `RuntimeError`, for instance -- exactly A3.2's finding) can ever wear the
`infra_failure` signature by accident. That narrowing, not the catch list, is the load-bearing
part of A3.2's fix. The full psql stderr stays server-side (`_log_infra_failure`, stderr --
this project's own house channel for a loud, non-silent, non-exposed diagnostic); the client
sees a generic message only, never SQL/role/schema/stack.

TIME AXIS (spec A3.1): every psql subprocess this module runs is bounded twice --
`PSQL_CONNECT_TIMEOUT_S = 5` (passed as the `PGCONNECT_TIMEOUT` envvar to the subprocess, so
libpq itself refuses a stalled TCP handshake/auth round trip rather than this process waiting on
the OS's own multi-minute default) and `PSQL_EXEC_TIMEOUT_S = 60` (`subprocess.run(timeout=...)`,
which covers a peer that accepts the connection and then goes silent -- a blackhole/accept-and-
stall server, the class no libpq connect-timeout option reaches). A `subprocess.TimeoutExpired`
on either bound is caught in exactly one place (`_psql`) and re-raised as `PsqlInfraFailure` --
a stall IS infra, the same typed 503 path as an ordinary connection refusal (A3.1, verbatim: "a
stall IS infra"). The write handlers are plain `def`, not `async def` -- FastAPI/Starlette runs a
plain `def` route in its threadpool, off the event loop, so one write blocked on
`PSQL_EXEC_TIMEOUT_S` cannot starve `/health` or any other route the way an `async def` calling
the blocking subprocess directly on the loop would (A3.1's amplifier finding). The read routes
were already plain `def` (this module never had an `async def` read route); only the four write
handlers changed shape.

PARSE CLOSURE (spec A3.2): the write routes decode and `json.loads` the raw body themselves
(A2.2's own choice, needed for the size checkpoints) -- which means they, not FastAPI's own
automatic body-parsing, own that decode's exception surface too. Three ways it can fail that are
NOT "malformed JSON" in the ordinary sense: invalid UTF-8 (`bytes.decode` raises
`UnicodeDecodeError`, a `ValueError` subclass), a numerically enormous integer literal (CPython's
int-string conversion raises `ValueError` past its digit-length guard), and deeply nested
brackets (the recursive-descent JSON parser raises `RecursionError`, which subclasses
`RuntimeError` -- exactly why the A2.4 handler had to narrow to `PsqlInfraFailure` rather than
catching `RuntimeError`, or this class would silently wear the wrong typed shape again). All
three are caught as `except (ValueError, RecursionError)` around the explicit decode+parse and
turned into one typed 422 that names WHICH axis failed (encoding / value magnitude / structure)
-- never echoing the raw body bytes back to the client (the body is untrusted and may not even
be valid UTF-8).

VALUE CLOSURE AND EXIT-CODE FIDELITY (spec A4). Two more axes close at the write parse boundary,
after structure/encoding/magnitude above and before psql: non-finite numbers
(`_reserialize_or_value_axis_failure`, `json.dumps(..., allow_nan=False)` -- Infinity/NaN/a
too-large-to-be-finite literal like `1e400`) and Postgres-text-representability
(`_representability_axis_failure` -- a literal U+0000 or an unpaired UTF-16 surrogate, neither
of which jsonb can store). Both are typed 422, naming the axis, never echoing the payload. On
the READ side, every id-typed path/query parameter is bounded `0 <= id <= MAX_ID`
(`_out_of_range_id`, symmetric with A2.6's `after_id >= 0`) -- typed 422 outside that domain,
before the value ever reaches psql's bigint cast. And `_query_json` now draws an exit-code line
PsqlInfraFailure alone used to blur: psql exit 2 (connection-level) still raises
`PsqlInfraFailure` (typed 503); exit 3 (a script/data-level SQL failure under `ON_ERROR_STOP=1`)
or any other residue raises the DEDICATED `PsqlUnclassifiedFailure` (typed 500
`unclassified_failure`) instead -- after A4.1/A4.2 close the value/id classes, this path is
unreachable via an ordinary request, so its occurrence names a boundary or deployment defect,
and the message says so honestly rather than asserting a cause (infra vs request) this boundary
did not witness.

A5 HARDENING (iteration-3 independent re-review). Five more findings, closed here:

1. **Representability-scan regression, fixed (A5.1).** A4.1(b)'s scan was denominated on the
   *escaped* serialization (`json.dumps(payload)`'s output text), so a payload whose string
   content is the literal six characters (a backslash followed by u0000 -- documenting an
   escape, never a NUL codepoint) re-escapes its own backslash to `\\u0000`, which CONTAINS the
   same six-character substring the old scan matched on -- a false positive wearing a
   lying message ("contains a NUL") for a payload jsonb stores fine. `_representability_axis_failure`
   now walks the ACTUAL codepoints of the PARSED value (every string and every object key,
   recursively -- `_iter_strings`), refusing only a real U+0000 character or a real unpaired
   UTF-16 surrogate CODE POINT (a lone `\\ud800`-class escape that `json.loads` decodes to an
   actual surrogate character precisely because it could not pair it with a following low
   surrogate -- a legitimate astral character always decodes to ONE composed non-surrogate
   code point). No serialization-mode text scan remains in this function at all.
2. **Write-payload integer-field domain (A5.2).** `boundary_models.py`'s per-surface
   `*WriteIntFields` models are the enumeration authority for "every integer-typed field the
   payload contract declares" -- `_bound_write_payload_ints` walks a surface's declared field
   names, and for each one the CALLER actually supplied, bounds it (or, for `enacts`'
   `bigint[]` shape, each element) to `0 <= v <= MAX_ID`, typed 422 naming the field and the
   bound. This is the id-domain class (A4.2) completed from path/query onto the write body --
   no other semantic validation is added; an absent field, or a present field holding a
   non-integer JSON value, is left for the kernel's own rowtype cast to judge (that is a type
   question, not a domain-bound question).
3. **The body-read time leg (A5.3).** `BODY_READ_TIMEOUT_S = 30` bounds the RAW BODY READ
   PHASE itself (`_bounded_raw_body`, via `asyncio.wait_for`) -- distinct from A3.1's
   `PSQL_CONNECT_TIMEOUT_S`/`PSQL_EXEC_TIMEOUT_S`, which bound the psql phase AFTER the body is
   already fully read. Before this bound existed a trickled body (a client sending a
   declared-length body a few bytes at a time) held the request open indefinitely; expiry
   raises `_BodyReadTimeout`, caught by its own exception handler, typed HTTP 408
   `{"disposition": "body_read_timeout", "timeout_s": ..., "message": ...}`.
4. **Pagination on all four read routes (A5.4).** `/standing/principals` and `/work/items`
   previously accepted no `limit`/`after_id` at all (silently served the whole view) -- they
   now carry the SAME `1 <= limit <= 1000`, `after_id >= 0` (and `<= MAX_ID`) discipline as
   `/rows/current`/`/credited`. `principal_standing_current` carries `id` (the view's own
   `p.id`), so it is bounded/ordered exactly like the other id-keyed views. `work_item_current`
   carries NO id column at all (one row per `slug`, no bigint key) -- the fixer's honest
   fallback, flagged per the spec's own "fixer flags if a view lacks one" clause: a
   `row_number() OVER (ORDER BY slug)` ordinal, computed in THIS SERVICE'S OWN wrapper query
   (never stored, never claimed to be a kernel id), is the cursor `after_id` compares against;
   the synthetic ordinal is stripped back out of each row's JSON before it is returned (`-
   'rn'`), so the served row shape is byte-identical to the view's own columns -- only the
   PAGINATION mechanics, not the data, differ from the id-keyed routes.
5. **Framework-owned coercion (A5.5) -- unchanged, named in the README**, per the A3.3
   precedent: no code change.

A7 FOLLOW-UP (iteration-5 confirmation pass): `_representability_axis_failure`'s own
traversal (`_iter_strings`, A5.1) is recursive and inherited none of A3.2's parse-time
recursion-depth protection -- a well-formed body nested deeply enough overflowed AFTER
parse, inside this scan, escaping every registered handler as a bare 500. The call site
now runs under the same `except RecursionError` A3.2's own parse catch uses, via the
same `_classify_parse_failure` classifier, so this joins the structure axis with an
identical typed-422 shape -- the caller sees no difference from A3.2's own deep-nesting
refusal; only the overflowing frame differs.

ADMISSION AXIS (spec A9, iteration-7 confirmation pass): A3.1 bounded PER-REQUEST psql time
(`PSQL_CONNECT_TIMEOUT_S`/`PSQL_EXEC_TIMEOUT_S`) and made the write handlers plain `def` so one
stalled write cannot starve `/health` on the SAME thread -- but A3.1's own adjacent axis, N
CONCURRENT stalled requests, was never reached: witnessed with measurements, N stalled requests
exhaust the shared ASGI threadpool (anyio's default 40 tokens on the review host) and wall-clock
on every route, `/health` included, grows unboundedly with N (80 -> 5.3s, 200 -> 27.7s, 600 ->
no answer in 180s) -- per-request time was bounded, *queueing* was not. **Fix: bounded admission
at the ONE choke point every kernel call already passes through.** `_psql` -- not each handler
individually -- acquires a slot from `_KERNEL_CALL_SEMAPHORE` (`threading.BoundedSemaphore`,
thread-safe, matching the plain-`def`/threadpool handler shape) via a NON-BLOCKING `acquire`,
as late as honesty allows (immediately before `subprocess.run`, never around this module's own
cheap Python setup) and releases it in a `finally` on every exit path (success, timeout, OS
error alike). `MAX_INFLIGHT_KERNEL_CALLS = 24` -- deliberately under the threadpool's 40 tokens,
so non-kernel work and `/health`'s own thread dispatch are never starved by kernel-call
occupancy alone. On saturation, `_psql` raises `KernelCallSaturated` WITHOUT ever calling
`subprocess.run` -- the caller is refused before it would have waited on anything, never
queued -- and the app's ONE dedicated exception handler for that class returns typed 503
`{"disposition": "server_saturated", "inflight_limit": 24, "message": ...}` (ADR-0012 P1: one
handler, not a try/except duplicated per route). Because gating lives in `_psql` rather than in
each handler, EVERY kernel-call site shares the same bound automatically -- reads, writes
(including a write's own two sequential kernel calls, the s43 capability probe and the boundary-
function call itself, each independently gated), and `/health`'s own several kernel probes
(`capability_manifest`, `service_principal_name`) alike -- with no second, handler-level
literal to keep in sync (the implementation-detail threadpool size stops being load-bearing:
this service's own named constant is the bound now). Preserved: the A1 transport, the A3.1
plain-`def` handler shape, every existing typed shape -- this axis adds one new one beside them,
never replacing or loosening any.

PAGINATION ON THE HISTORY ROUTE (spec A10, iteration-8 confirmation pass): `GET
/rows/{id}/history` was the one read route the A5.4 pagination pass never enumerated -- it
returned the ENTIRE supersession chain unconditionally, silently discarding any `limit`/
`after_id` a caller supplied (witnessed: `limit=1&after_id=0` returned the same ~620 KB, 400-row
body as no parameters at all). Fix: the SAME `1 <= limit <= 1000` / `after_id >= 0` discipline as
`/rows/current`/`/credited`/`/standing/principals`/`/work/items`, checked in the SAME order and
returning the SAME typed-422 message family (`_out_of_range_id`, the shared bound). The
pagination cursor is the history hop's OWN row id (`after_id` compares against each returned
row's `id`, `ORDER BY id LIMIT limit`, the same id-keyed shape `/rows/current` already uses) --
the chain-computing CTE is unchanged, only an outer paging query is added, so every hop remains
reachable across pages and each row's `superseded_by` pointer is untouched. The one deliberate
divergence from the other four routes: this route's OWN default `limit` is
`HISTORY_DEFAULT_LIMIT = 1000`, not the others' 100 -- see that constant's own docstring for why
(a short chain fetched with no parameters at all must stay byte-identical to the pre-A10
response, and a 100-row default would have silently started truncating chains the old,
unpaginated route never truncated).

CURSOR HONESTY ON THE SLUG-KEYED ROUTE; THE HISTORY ROUTE'S NOT-FOUND SHAPE (spec A11,
iteration-9 confirmation pass). Two uniformity completions:

1. `GET /work/items`' pagination was unstable under concurrent insertion -- its pre-A11 cursor
   was a `row_number() OVER (ORDER BY slug)` ordinal RECOMPUTED PER REQUEST, so an item inserted
   mid-walk with a slug sorting before an already-served item shifted every ordinal after it
   (witnessed: pages `[aa,cc]` then `[cc,ee]` served, against a view reading
   `[aa,bb,cc,ee,gg]` -- `cc` served twice, `bb` never; every individual response was well-typed,
   the UNION was silently wrong). Fix: the cursor re-keys to the view's own TRUE key,
   `after_slug` (keyset `WHERE slug > :after_slug ORDER BY slug`, same `limit` domain, same
   message family) -- the synthetic ordinal is retired outright, and a supplied `after_id` on
   THIS route refuses typed 422 teaching `after_slug` (never silently ignored -- A10's own
   lesson). Honesty bound, stated rather than overclaimed: a slug keyset structurally eliminates
   duplication (a served slug can never be re-served -- the cursor is a VALUE, not a POSITION),
   but a row inserted BEHIND an in-flight cursor is not visible to that walk, and cannot be under
   any snapshot-free scheme over a non-append-monotonic key (ledger ids are append-monotonic,
   exactly why `/rows/current` carries the STRONGER guarantee; slugs are not) -- that residual is
   this route's NAMED, disclosed semantics: no duplicates ever; the page union equals the view
   restricted to slugs beyond the cursor's progression; an item inserted behind the cursor
   appears on the next walk. `after_slug` domain: text, byte-length bounded by
   `MAX_AFTER_SLUG_BYTES = 512` (typed 422 beyond it -- a slug over 512 bytes names no real item
   any world this kernel scaffolds), any in-domain value is a valid cursor position (keyset
   semantics require no existence check). The slug crosses to psql as a BOUND `-v` argument
   (`_query_json(..., extra_v={"after_slug": after_slug})`), the same injection-safe
   substitution the write routes already use for payload bodies -- never spliced as SQL text.
2. `GET /rows/{id}/history` answered `200 []` for a nonexistent row where sibling `GET
   /rows/{id}` typed-404s the identical input class -- and the empty array was only an INFERRED
   nonexistence signal (an existing row always contributes at least its own hop). Fix: a leading
   existence check (`_row_not_found`, shared with `row_by_id`'s own 404 shape, ADR-0012 P1) --
   a nonexistent in-domain id gets the sibling route's EXACT typed 404 (`"no row N"`); existing
   rows are unaffected, and the recursive supersession CTE runs only after the check passes.

THE QUERY-DERIVED STRING JOINS THE REPRESENTABILITY CLOSURE (spec A12, iteration-10 confirmation
pass). A11's `after_slug` gained the 512-byte length bound but not A4.1(b)'s representability
gate at birth -- a literal U+0000 or an unpaired UTF-16 surrogate, inside the 512-byte domain,
reached `_psql` unchecked and detonated in `subprocess.run` as an uncaught `ValueError: embedded
null byte` (a bare untyped 500). The rule (A4.1(b): a literal NUL or an unpaired surrogate is
not Postgres-text-representable) is now stated ONCE (`_representability_failure_for_string`) and
audited at BOTH ingresses: the write-payload scan (`_representability_axis_failure`) and the
read-side query-parameter gate (`_query_string_representability_failure`, applied to
`after_slug` in `work_items`, checked after the length bound and before the value crosses to
psql's `-v` argument). ENUMERATION (A12's own mandate, not assumed): every string-typed
path/query parameter across this service's eleven routes was read from its route signature --
`after_slug` on `GET /work/items` is the ONLY one; every other path/query parameter (`row_id`,
`after_id`, `limit`) is `int` or `int | None`. Choke-point net, A8's `OSError` pattern repeated:
`_psql` also catches a bare `ValueError` from `subprocess.run` itself and raises the typed
unclassified-failure path, so no future string-typed parameter, however added, can wear the
bare shape even if its own ingress gate is missed.

THE DUMPS-SIDE RECURSION NET (spec A13, post-fixpoint microamendment, ledger row 1621). Not a
finding -- `_reserialize_or_value_axis_failure`'s own `json.dumps` call had no `RecursionError`
handling of its own and was protected only by the accident that `json.loads` overflows at the
same-or-shallower depth on this CPython build; no caller input reaches it today. Designed
safety now replaces that accidental safety: the call gains `except RecursionError`, joining the
SAME typed 422 structure-axis refusal A7 already gave the adjacent post-parse traversal -- one
clause, same message family, no behavior change for any input that parses today.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import is top-of-file.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import JSONResponse

# Path setup, NOT lazy imports (both `sys.path.insert` calls execute at module import time,
# unconditionally, before either import below runs -- the gate that actually arbitrates this,
# gates/no_lazy_imports.py, passes on this file). Both inserts are needed regardless of HOW
# this module is invoked: `python3 -m serving.boundary_service` (spec §2's launch command)
# puts the REPO ROOT on sys.path[0], not serving/ itself, so the sibling import below
# (`boundary_models`, a top-level import for house-convention consistency with every other
# filing/ consumer, not a package-relative one) needs its own directory added explicitly.
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "filing"))
import deployment_record  # filing/deployment_record.py -- the ONE home for the deployment.json shape  # noqa: E402

from boundary_models import (  # noqa: E402
    BodyReadTimeout,
    CapabilityAbsent,
    CapabilityManifest,
    HealthResponse,
    InfraFailure,
    LedgerWriteIntFields,
    ObligationWriteIntFields,
    PayloadTooLarge,
    RegistrationWriteIntFields,
    ReviewWriteIntFields,
    ServerSaturated,
    UnclassifiedFailure,
)

# The four s43 boundary functions, named ONCE (ADR-0012 P1) -- the write-route table (spec §4)
# is built from this dict, never re-typed per route.
WRITE_SURFACES: dict[str, str] = {
    "ledger": "ledger_write",
    "review": "review_write",
    "registration": "registration_write",
    "obligation": "obligation_write",
}

# A5.2: per-surface pydantic models are the ENUMERATION AUTHORITY for "every integer-typed
# field the payload contract declares" (boundary_models.py's own docstrings name each
# surface's kernel source of truth for its field list). `_bound_write_payload_ints` below
# consults ONLY these models' declared field names -- never the payload's own keys -- so an
# unknown/unexpected key is left entirely to the kernel's own key-membership check (spec §4);
# this dict adds no new key-membership judgment, only a value-domain bound on keys the model
# already declares.
WRITE_SURFACE_INT_FIELDS: dict[str, type] = {
    "ledger": LedgerWriteIntFields,
    "review": ReviewWriteIntFields,
    "registration": RegistrationWriteIntFields,
    "obligation": ObligationWriteIntFields,
}

# A deployment.json identifier (schema/kern/role) must look like a plain SQL identifier --
# refused at construction time otherwise (ADR-0002 rung 1); this is the one guard that lets
# every query below interpolate schema/kern/role as bare text safely.
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}

# A2.2's raw-body write-ingress bound (ADR-0012 P1: one home, not one literal per checkpoint),
# 1 MiB -- generous for any ledger payload. Enforced at `_read_bounded_body` (checkpoint a,
# raw body, BEFORE any JSON parsing); its rationale is BUFFERING -- never hold an unbounded
# request body in memory. As of A8 this constant no longer denominates checkpoint (b): A2.2
# justified 1 MiB as "safely under the argv wall (ARG_MAX = 2 MiB total)", but the payload
# crosses as ONE psql `-v` argument and the PER-ARGUMENT wall is MAX_ARG_STRLEN (131 072
# bytes) -- see MAX_PSQL_ARG_BYTES below. See this module's docstring, "SIZE AXIS".
MAX_WRITE_BODY_BYTES = 1_048_576

# A8 item 1: checkpoint (b)'s OWN bound, denominated on the transport's TRUE capacity -- the
# re-serialized payload travels to postgres as ONE psql `-v payload=...` argument, and Linux
# bounds each individual exec argument at MAX_ARG_STRLEN (32 pages = 131 072 bytes), NOT the
# 2 MiB total-argv ARG_MAX the pre-A8 bound was sized against. 100 000 sits under
# MAX_ARG_STRLEN with margin (a ledger payload is prose; this remains generous -- A2.2's own
# "generous" claim, re-made honestly at the smaller number). The A1-ratified psql transport is
# NOT reopened: the bound moves to the transport's true capacity, not the transport to the
# bound. Enforced in `make_write_route`'s handler (checkpoint b), typed 413 naming this wall.
MAX_PSQL_ARG_BYTES = 100_000

# A3.1's two named time-axis bounds (ADR-0012 P1: one home each, not a literal per call site).
# PSQL_CONNECT_TIMEOUT_S bounds the TCP handshake/auth round trip (passed as PGCONNECT_TIMEOUT
# so libpq itself enforces it); PSQL_EXEC_TIMEOUT_S bounds the whole subprocess (covers a peer
# that accepts the connection and then goes silent -- a stall, the class no libpq connect-
# timeout option reaches). See this module's docstring, "TIME AXIS".
PSQL_CONNECT_TIMEOUT_S = 5
PSQL_EXEC_TIMEOUT_S = 60

# A5.3: the body-READ phase's own time bound (ADR-0012 P1: one named constant), distinct from
# the two psql-phase bounds directly above -- those start their clock only AFTER the body is
# already fully in hand. Before this bound existed, a trickled body (a client sending a
# declared-length body a few bytes at a time) held the request open indefinitely (48s
# witnessed in A5's own review). Enforced in `_bounded_raw_body` via `asyncio.wait_for` around
# the whole `_read_bounded_body` read loop.
BODY_READ_TIMEOUT_S = 30

# A4.2: the read-side id domain, symmetric with A2.6's `after_id >= 0` -- every id-typed
# path/query parameter is bounded `0 <= id <= MAX_ID` (a Postgres `bigint`'s own upper bound,
# 2**63 - 1). Named ONCE (ADR-0012 P1) rather than re-derived per route; before this bound
# existed, an over-range id reached psql's bigint cast unchecked and wore a 503 it did not
# earn (A4's own trigger: only a genuine connection-level failure should ever wear that shape).
# A5.2 reuses this SAME constant to bound integer-typed WRITE-payload fields too (the id-domain
# class, completed from path/query onto the write body).
MAX_ID = 2**63 - 1

# A9: the concurrency admission bound (ADR-0012 P1: one named constant, not a per-handler
# literal). Deliberately UNDER the ASGI threadpool's own default concurrency (anyio's 40 tokens
# on the review host) so kernel-call occupancy alone can never starve non-kernel work or
# /health's own thread dispatch -- the threadpool size stops being load-bearing; this service's
# own named constant is the bound. `_KERNEL_CALL_SEMAPHORE` is the ONE shared gate every kernel
# call passes through (see `_psql`'s own docstring, "ADMISSION AXIS"); `threading.BoundedSemaphore`
# is thread-safe and matches the plain-`def`/threadpool handler shape A3.1 already established
# (a real OS thread per in-flight handler, not a coroutine).
MAX_INFLIGHT_KERNEL_CALLS = 24
_KERNEL_CALL_SEMAPHORE = threading.BoundedSemaphore(MAX_INFLIGHT_KERNEL_CALLS)

# A10: GET /rows/{id}/history's OWN default `limit` -- deliberately 1000, not the 100 every
# other paginated route defaults to (ADR-0012 P1 note: this is the one place the four A5.4
# routes' shared default is NOT reused, named here rather than silently diverging). A10's own
# adjudication requires a short chain fetched WITH NO QUERY PARAMETERS to be byte-identical to
# the pre-A10 unpaginated response; the pre-A10 route never truncated, so the post-A10 default
# must not either for the overwhelmingly common short-chain case -- 1000 is the same ceiling
# `limit` is bounded to everywhere else in this service, so "no parameters" and "the largest
# honored page" coincide by construction, and only a chain longer than 1000 hops (unseen in
# this project's own worlds) needs an explicit `after_id` hop to see the rest.
HISTORY_DEFAULT_LIMIT = 1000

# A11 item 1: `/work/items`' cursor domain bound -- the per-field reasoning A8's transport wall
# already applied to a single argument's own margin, applied here to ONE field (never a general
# string-length policy): a slug over 512 bytes names no real item any world this kernel
# scaffolds could ever open (work_slug is operator-authored identifier text, not free prose), so
# 512 is generous headroom, not a measured ceiling. Named ONCE (ADR-0012 P1) rather than an
# inline literal at the one call site that checks it.
MAX_AFTER_SLUG_BYTES = 512


class PsqlInfraFailure(Exception):
    """A3.2's narrowing, NARROWED FURTHER per A4.3: the ONE exception class a genuinely
    connection-level psql failure -- psql exit 2 (unreachable world, connection refusal) or a
    PSQL_EXEC_TIMEOUT_S stall -- is raised as. The app's single exception handler (`create_app`)
    catches ONLY this class -- never a bare `RuntimeError`, so a foreign exception that happens
    to subclass `RuntimeError` (`RecursionError`, for instance) can never wear the
    `infra_failure` HTTP shape by accident. As of A4.3 this class no longer covers psql exit 3
    or any other nonzero residue -- see `PsqlUnclassifiedFailure` below; `_query_json` is the
    ONE place that draws the exit-code line between the two."""


class PsqlUnclassifiedFailure(Exception):
    """A4.3: the sibling narrowing to `PsqlInfraFailure` above. A psql exit that is NEITHER
    exit 2 (connection-level) NOR a kernel verdict -- concretely psql exit 3 (a script/data-
    level failure under `ON_ERROR_STOP=1`) or any other unrecognized nonzero residue -- is
    raised as THIS class, never `PsqlInfraFailure`: after A4.1/A4.2 close the value-closure and
    id-domain classes at the parse/read boundary, this path is unreachable via an ordinary
    caller-supplied request, so its occurrence means a boundary or deployment defect, not a
    request defect -- a `PsqlInfraFailure` (typed 503, "not a problem with your request") would
    be an actively false cause statement for this case (the lying-signature class, ADR-0002
    rung 3). The app's single exception handler for this class returns typed 500
    `unclassified_failure`, honest about not knowing the cause; full detail logged server-side
    only, exactly like `PsqlInfraFailure`'s own logging discipline."""


class KernelCallSaturated(Exception):
    """A9: raised by `_psql` -- and ONLY `_psql`, the one shared choke point every kernel call
    passes through -- when `_KERNEL_CALL_SEMAPHORE`'s `MAX_INFLIGHT_KERNEL_CALLS` slots are all
    held by other in-flight kernel calls and this call's own non-blocking `acquire` fails.
    Raised BEFORE `subprocess.run` is ever invoked (never after a stall, never after a timeout --
    the caller is refused before it would have waited on anything), so this is an ordinary,
    expected, load-driven condition, not an infra anomaly: it deliberately does NOT share
    `PsqlInfraFailure`'s or `PsqlUnclassifiedFailure`'s server-side logging discipline (there is
    nothing here a server-side log would explain that the typed response itself does not already
    say). The app's single exception handler for this class returns typed 503
    `server_saturated`, naming the bound, the cause, and that retry-with-backoff is the correct
    caller response (spec A9, verbatim)."""


class BoundaryConfig:
    """This deployment's resolved (db, host, schema, kern, role) plus the psql connection
    host -- kept distinct from the LEDGER's own `host` field on purpose: `deployment.json`'s
    `host` is the POSTGRES host (what `led`/`judge` already call `--host`), never this HTTP
    service's own bind address (spec §2's separate `--host`/`--port` argv)."""

    def __init__(self, record: deployment_record.DeploymentRecord) -> None:
        for field_name in ("schema", "kern", "role"):
            value = getattr(record, field_name)
            if not _IDENT_RE.match(value):
                raise SystemExit(
                    f"boundary_service: REFUSED at start-up -- deployment.json field "
                    f"'{field_name}'={value!r} is not a plain SQL identifier "
                    f"(pattern {_IDENT_RE.pattern}). A deployment record is operator-authored "
                    f"config, not HTTP input, but this service still refuses to interpolate an "
                    f"unvalidated identifier into SQL text (ADR-0002 rung 1, construction-time)."
                )
        self.record = record

    @property
    def pg_host(self) -> str:
        return self.record.host

    @property
    def db(self) -> str:
        return self.record.db

    @property
    def schema(self) -> str:
        return self.record.schema

    @property
    def kern(self) -> str:
        return self.record.kern

    @property
    def role(self) -> str:
        return self.record.role


def _psql(cfg: BoundaryConfig, script: str, extra_v: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run `script` against this deployment's postgres, as the granted role, with search_path
    set to (schema, kern) -- the ONE connection idiom every query/call in this module uses (the
    same pattern bootstrap/templates/led.tmpl's own kernel_write()/psql_tuples() helpers use).
    `extra_v` values cross as psql `-v` bind vars (never string-spliced).

    A3.1's time axis, bounded twice: `PGCONNECT_TIMEOUT` in the subprocess's OWN environment
    (never the parent's -- a fresh dict copy) bounds the TCP handshake/auth round trip at libpq
    itself; `subprocess.run(timeout=PSQL_EXEC_TIMEOUT_S)` bounds the whole process, catching a
    peer that accepts the connection and then stalls (the class no libpq connect-timeout option
    reaches). `subprocess.TimeoutExpired` is caught in this ONE place and re-raised as
    `PsqlInfraFailure` -- a stall IS infra (A3.1, verbatim).

    A9's admission axis, bounded once more: immediately before `subprocess.run` -- as late as
    honesty allows, never around this function's own cheap Python setup above -- this function
    acquires a NON-BLOCKING slot from `_KERNEL_CALL_SEMAPHORE` (`MAX_INFLIGHT_KERNEL_CALLS`
    concurrent kernel calls, shared server-wide across every call site: reads, writes, and
    `/health`'s own kernel probes alike). On saturation the acquire fails immediately and this
    function raises `KernelCallSaturated` WITHOUT ever calling `subprocess.run` -- refused before
    it would have waited on anything, never queued (A9, verbatim: "never queues unboundedly").
    On every path past that point -- success, `TimeoutExpired`, `OSError`, or `ValueError` -- the
    slot is released in a `finally`, released as early as honesty allows (the instant
    `subprocess.run` itself returns or raises, not deferred to the caller).

    A12's choke-point net, A8's `OSError` pattern repeated: `ValueError` from `subprocess.run`
    itself (concretely, "embedded null byte" -- Python's own argv-encoding layer raises this
    when ANY `args`/`extra_v` string reaching this call carries a literal NUL, regardless of
    which route or future parameter put it there) is caught HERE, at the one choke point every
    kernel call already passes through, and re-raised as the typed unclassified-failure path.
    This is defense in depth, not the primary mechanism -- the primary mechanism is the
    representability gate at each ingress (A4.1(b) for write payloads, A12's
    `_query_string_representability_failure` for `after_slug`) -- but it means no future
    string-typed parameter, however added, can ever let a bare `ValueError` escape this
    function's own callers."""
    args = ["psql", "-h", cfg.pg_host, "-d", cfg.db, "-tAq", "-v", "ON_ERROR_STOP=1"]
    for k, v in (extra_v or {}).items():
        args += ["-v", f"{k}={v}"]
    args += ["-f", "/dev/stdin"]
    preamble = f"SET ROLE {cfg.role};\nSET search_path = {cfg.schema}, {cfg.kern};\n"
    env = dict(os.environ)
    env["PGCONNECT_TIMEOUT"] = str(PSQL_CONNECT_TIMEOUT_S)
    if not _KERNEL_CALL_SEMAPHORE.acquire(blocking=False):
        raise KernelCallSaturated(
            f"the service already has MAX_INFLIGHT_KERNEL_CALLS={MAX_INFLIGHT_KERNEL_CALLS} "
            f"concurrent kernel calls in flight (spec A9) -- this call is refused immediately "
            f"rather than queued. The cause is ordinary concurrent load, not a defect in this "
            f"request; the correct response is to retry after a short backoff."
        )
    try:
        return subprocess.run(
            args, input=preamble + script, capture_output=True, text=True,
            env=env, timeout=PSQL_EXEC_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as e:
        raise PsqlInfraFailure(
            f"psql subprocess exceeded PSQL_EXEC_TIMEOUT_S={PSQL_EXEC_TIMEOUT_S}s without "
            f"exiting -- a stalled peer (accept-then-silent), not an ordinary connection "
            f"refusal (that would have exited well within the bound). Treated as infra "
            f"failure (A3.1: a stall IS infra)."
        ) from e
    except OSError as e:
        # A8 item 1(ii), defense in depth (NOT the primary mechanism -- checkpoint (b)'s
        # MAX_PSQL_ARG_BYTES bound is): an OSError from the subprocess launch itself (E2BIG
        # when an argument exceeds the kernel's MAX_ARG_STRLEN transport wall, ENOENT if the
        # psql binary is absent, or any sibling) is a boundary/deployment defect, not a
        # connection-level infra fact -- it takes the typed unclassified-failure path (500)
        # so no present or future transport wall can ever wear the bare untyped shape §9
        # forbids. Full detail stays server-side, per the class's own logging discipline.
        raise PsqlUnclassifiedFailure(
            f"psql subprocess could not be launched (OSError before any connection was "
            f"attempted -- e.g. E2BIG past the kernel's per-argument MAX_ARG_STRLEN wall, or "
            f"a missing psql binary): {e}"
        ) from e
    except ValueError as e:
        # A12: the choke-point net, A8's OSError pattern repeated -- a bare ValueError from
        # `subprocess.run` itself (e.g. "embedded null byte" in an argv/-v string) is a
        # boundary/deployment defect exactly like an OSError launch failure above, never a
        # connection-level infra fact. Defense in depth: the primary mechanism is the
        # representability gate at each ingress (A4.1(b), A12's own query-string gate); this
        # is the net that catches whatever a future ingress fails to gate at its own boundary.
        raise PsqlUnclassifiedFailure(
            f"psql subprocess could not be launched (ValueError before any connection was "
            f"attempted -- e.g. an embedded NUL byte in an argument this function's own "
            f"representability gates should have refused upstream): {e}"
        ) from e
    finally:
        # A9: released as early as honesty allows -- the instant subprocess.run itself returns
        # or raises, on EVERY exit path (success and both exception paths above alike). Only
        # reached when the slot was actually acquired (the saturation raise above returns before
        # entering this try/finally at all, so there is no double-release to guard against).
        _KERNEL_CALL_SEMAPHORE.release()


def _query_json(cfg: BoundaryConfig, sql: str, extra_v: dict[str, str] | None = None) -> Any:
    """Run a SELECT of exactly one scalar column; parse and return it as a Python value.
    On a nonzero psql exit, raises EXACTLY ONE of two dedicated exceptions -- never silently
    returning None/empty for a REAL failure -- per A4.3's exit-code fidelity: psql under
    `ON_ERROR_STOP=1` reliably distinguishes exit 2 (connection-level failure -- unreachable
    world, connection refusal: genuinely infra) from exit 3 or any other residue (a script/
    data-level failure the write/read path reaches with values that are valid JSON yet not
    Postgres-representable, or any other unrecognized nonzero exit). Exit 2 raises
    `PsqlInfraFailure` (typed 503, "not a problem with your request" -- now TRUE, since A4.1/
    A4.2 close the value-closure and id-domain classes that used to reach exit 3 through this
    same path). Exit 3 and any other residue raise `PsqlUnclassifiedFailure` (typed 500,
    honest that the boundary does not know the cause) -- conflating the two, as the
    pre-A4 code did (every nonzero exit wearing `PsqlInfraFailure`), is exactly the
    lying-signature class A4 exists to close: a handful of cheap malformed-but-not-invalid-
    JSON payloads should never counterfeit outage signal in the infra logs.

    A ZERO-ROW or SQL-NULL result is NOT either failure: `psql -tAq` prints the empty string
    for a NULL scalar (never the text "null"), and a single-row subquery over a WHERE that
    matches nothing legitimately returns zero output rows -- both are the honest "no value"
    case every caller here already handles (row_by_id's 404; service_principal_name's absent-
    registration None), so both map to Python None rather than an error. Distinguishing
    "no value" from "the query itself broke" is exactly the returncode check below, not
    output-emptiness -- conflating them would turn a legitimate NULL into a manufactured
    500/503 on every one of this service's read routes."""
    cp = _psql(cfg, sql, extra_v)
    if cp.returncode == 2:
        raise PsqlInfraFailure(f"psql query failed (exit {cp.returncode}, connection-level): {cp.stderr.strip()[-2000:]}")
    if cp.returncode != 0:
        raise PsqlUnclassifiedFailure(
            f"psql query failed (exit {cp.returncode}, NOT connection-level -- a script/data-"
            f"level residue A4.1/A4.2's closures should have made unreachable via an ordinary "
            f"request; this is a boundary or deployment defect, not a request defect): "
            f"{cp.stderr.strip()[-2000:]}")
    lines = [ln for ln in cp.stdout.splitlines() if ln.strip()]
    if not lines:
        return None
    return json.loads(lines[-1])


def _regclass_exists(cfg: BoundaryConfig, qualified_name: str) -> bool:
    out = _query_json(cfg, f"SELECT to_jsonb(to_regclass('{qualified_name}') IS NOT NULL);")
    return bool(out)


def capability_manifest(cfg: BoundaryConfig) -> CapabilityManifest:
    """Live per-request detection (no caching, spec §5) -- object existence only, never a
    version literal (module docstring)."""
    s22 = _regclass_exists(cfg, f"{cfg.schema}.work_item_current")
    s41 = _regclass_exists(cfg, f"{cfg.schema}.principal_relations")
    credited = _regclass_exists(cfg, f"{cfg.schema}.credited_current")
    s43 = bool(_query_json(
        cfg,
        f"SELECT to_jsonb(EXISTS (SELECT 1 FROM pg_proc p JOIN pg_namespace n "
        f"ON n.oid = p.pronamespace WHERE n.nspname = '{cfg.kern}' "
        f"AND p.proname = 'ledger_write' AND p.prosecdef));",
    ))
    return CapabilityManifest(s22_work=s22, s41_identity=s41, s43_boundary=s43, credited_view=credited)


def service_principal_name(cfg: BoundaryConfig) -> str | None:
    """A2.3: guarded with the SAME existence check every other capability fact uses
    (`_regclass_exists`, object existence never a version literal) -- on a world whose
    `kernel.principal` table itself is absent, this degrades to `None` exactly like every
    other capability-absent case, rather than reaching the query at all. `_query_json` already
    maps a legitimate zero-row/NULL result to `None` (see its own docstring); this guard covers
    the STRUCTURALLY absent case that same mapping cannot reach (a query against a table that
    does not exist is a psql error, not a NULL scalar)."""
    if not _regclass_exists(cfg, f"{cfg.kern}.principal"):
        return None
    out = _query_json(
        cfg,
        f"SELECT to_jsonb((SELECT name FROM {cfg.kern}.principal "
        f"WHERE name = 'boundary-service' AND agent_class = 'tool'));",
    )
    return out


def capability_absent(capability: str, message: str) -> JSONResponse:
    body = CapabilityAbsent(capability=capability, message=message)
    return JSONResponse(status_code=409, content=body.model_dump())


def payload_too_large(limit_bytes: int, observed_bytes: int, message: str) -> JSONResponse:
    """A2.2: the one typed shape both write-ingress size checkpoints return (ADR-0012 P1).
    As of A8 the two checkpoints carry two DIFFERENT bounds (MAX_WRITE_BODY_BYTES raw-body
    buffering; MAX_PSQL_ARG_BYTES re-serialized transport), so `limit_bytes` is supplied by
    the checkpoint that refused -- the shape stays one, and its numbers stay honest about
    which bound actually fired."""
    body = PayloadTooLarge(limit_bytes=limit_bytes, observed_bytes=observed_bytes, message=message)
    return JSONResponse(status_code=413, content=body.model_dump())


def infra_failure(message: str) -> JSONResponse:
    """A2.4, narrowed per A4.3: the one typed shape a genuinely connection-level psql failure
    (exit 2 or a timeout) returns."""
    body = InfraFailure(message=message)
    return JSONResponse(status_code=503, content=body.model_dump())


def unclassified_failure(message: str) -> JSONResponse:
    """A4.3: the one typed shape a psql exit 3 (or other unrecognized nonzero residue) returns
    -- HTTP 500, honest that this boundary does not know the cause, never claiming the
    connection-level `infra_failure` shape it did not earn."""
    body = UnclassifiedFailure(message=message)
    return JSONResponse(status_code=500, content=body.model_dump())


def server_saturated(message: str) -> JSONResponse:
    """A9: the one typed shape MAX_INFLIGHT_KERNEL_CALLS concurrent kernel calls already in
    flight returns -- HTTP 503, `inflight_limit` naming the bound this call was refused
    against, never claiming the connection-level `infra_failure` shape (this is ordinary load,
    not an infrastructure anomaly -- the two are deliberately distinct typed shapes)."""
    body = ServerSaturated(inflight_limit=MAX_INFLIGHT_KERNEL_CALLS, message=message)
    return JSONResponse(status_code=503, content=body.model_dump())


def _out_of_range_id(name: str, value: int) -> JSONResponse | None:
    """A4.2: the read-side id domain, applied identically to every id-typed path/query
    parameter (ADR-0012 P1 -- one check, named once, not re-derived per route) -- symmetric
    with A2.6's `after_id >= 0` precedent, now completed upward to `MAX_ID` (a Postgres
    `bigint`'s own ceiling). Returns the typed 422 when `value` is out of `[0, MAX_ID]`, else
    None (the caller proceeds). Closing this class here is what makes an over-range id refuse
    BEFORE it ever reaches psql's bigint cast -- previously it wore a 503 it did not earn."""
    if value < 0 or value > MAX_ID:
        return JSONResponse(status_code=422, content={
            "detail": f"{name} must satisfy 0 <= {name} <= {MAX_ID} (a Postgres bigint's own "
                      f"domain, spec §3/A2.6/A4.2); got {value}"})
    return None


def _row_not_found(cfg: BoundaryConfig, row_id: int) -> JSONResponse | None:
    """A11 item 2: the leading existence check `GET /rows/{id}/history` shares with its sibling
    `GET /rows/{id}` -- named ONCE (ADR-0012 P1) so a nonexistent in-domain id gets the IDENTICAL
    typed 404 shape (`{"detail": "no row N"}`) from both routes, never a route-local dialect.
    `row_by_id` below does not call this helper (it already fetches the full row in one round
    trip and 404s on a `None` result); this helper exists for a caller -- `row_history`, as of
    A11 -- that must know existence BEFORE doing any further work (the recursive supersession
    CTE, in `row_history`'s case), without first fetching the row's own content. Returns the
    typed 404 `JSONResponse` when `row_id` does not exist, else `None` (the caller proceeds)."""
    exists = bool(_query_json(
        cfg, f"SELECT to_jsonb(EXISTS (SELECT 1 FROM {cfg.schema}.ledger WHERE id = {row_id}));"))
    if not exists:
        return JSONResponse(status_code=404, content={"detail": f"no row {row_id}"})
    return None


def _log_infra_failure(context: str, exc: Exception) -> None:
    """The full, loud, un-redacted detail stays server-side (stderr -- this project's own house
    channel for a loud diagnostic every other construction-time refusal in this file already
    uses) -- never in the HTTP response (A2.4's exposure posture)."""
    sys.stderr.write(f"boundary_service: INFRA FAILURE ({context}): {exc}\n")


def _log_unclassified_failure(context: str, exc: Exception) -> None:
    """A4.3's sibling to `_log_infra_failure` -- the full detail (which, unlike an ordinary
    infra failure, may include the actual psql stderr naming the offending SQL/data) stays
    server-side only; the client sees `unclassified_failure`'s honest, cause-free message."""
    sys.stderr.write(f"boundary_service: UNCLASSIFIED FAILURE ({context}): {exc}\n")


class _BodyTooLarge(Exception):
    """Raised by `_read_bounded_body` (checkpoint a), via the `_bounded_raw_body` FastAPI
    dependency -- caught once, by the app-level exception handler (`create_app`), and turned
    into the typed `payload_too_large` response. Not caught inline in the write route itself
    (A3.1's plain-`def` shape) because the dependency runs BEFORE the (now synchronous, off-
    the-event-loop) handler is ever dispatched."""

    def __init__(self, observed_bytes: int, message: str) -> None:
        super().__init__(message)
        self.observed_bytes = observed_bytes
        self.message = message


def _classify_parse_failure(exc: Exception) -> tuple[str, str]:
    """A3.2's parse closure: classify a body decode/parse failure by the axis it violates --
    encoding / value magnitude / structure -- WITHOUT ever echoing the raw body bytes back (the
    body is untrusted and, in the encoding-axis case, may not even be valid UTF-8 to echo).
    `json.loads` on `bytes` decodes internally, so `UnicodeDecodeError` (a `ValueError`
    subclass), an oversized-integer-literal `ValueError` (CPython's int-string conversion
    guard), a `json.JSONDecodeError` (also a `ValueError` subclass), and a `RecursionError`
    (deep nesting overruns the recursive-descent parser's stack, and subclasses `RuntimeError`
    -- exactly why the infra handler above is narrowed to `PsqlInfraFailure` rather than a bare
    `RuntimeError`) are the four shapes this classifies."""
    if isinstance(exc, UnicodeDecodeError):
        return "encoding", f"the request body is not valid UTF-8 ({exc})"
    if isinstance(exc, RecursionError):
        return ("structure", "the request body nests too deeply for this service's JSON parser "
                              "to descend (a structural bound, not a size bound)")
    if isinstance(exc, json.JSONDecodeError):
        return "structure", f"the request body is not well-formed JSON ({exc})"
    if isinstance(exc, ValueError):
        return "value magnitude", f"a numeric literal in the request body is too large to parse ({exc})"
    return "structure", f"the request body could not be parsed ({exc})"  # pragma: no cover


def _reserialize_or_value_axis_failure(payload: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """A4.1(a): value closure at the parse boundary -- non-finite numbers. Re-serializes with
    `json.dumps(..., allow_nan=False)`: a parsed body can contain `Infinity`/`NaN` (Python's
    `json.loads` accepts these non-standard literals by default, and any numeric literal past
    float's exponent range, e.g. `1e400`, silently parses TO one of them) even though jsonb has
    no representation for them. `allow_nan=False` makes THIS re-serialization -- which is the
    ONE text that actually crosses to psql, the same call checkpoint (b)'s size bound already
    needed -- raise `ValueError` the instant such a value is present, rather than silently
    emitting the non-standard `Infinity`/`NaN`/`-Infinity` tokens psql would then choke on with
    an opaque, unclassified SQL error.

    A13 (post-fixpoint microamendment, ledger row 1621): this `json.dumps` call also gains
    `except RecursionError`, the same typed structure-axis refusal A7 already gave the
    adjacent post-parse traversal (`_iter_strings`/`_representability_axis_failure`). Before
    this, a deeply nested object reaching THIS call was protected only by the accident that
    `json.loads` overflows at the same-or-shallower depth on this CPython build -- not by any
    designed guarantee of this call's own. No caller input reaches this branch today (the
    loads-side guard fires first for every payload that ever parses); this replaces that
    accidental safety with a designed net, same message family as A7.

    Returns `(payload_json, None, None)` on success; on refusal, `(None, axis, detail)` naming
    WHICH axis failed -- `"value"` for a non-finite number (A4.1(a)), `"structure"` for A13's
    recursion net -- and the detail text, never echoing the payload back."""
    try:
        return json.dumps(payload, allow_nan=False), None, None
    except ValueError as e:
        return None, "value", (
            f"the payload contains a non-finite number (Infinity/NaN, or a numeric "
            f"literal magnitude too large to represent as a finite float) that "
            f"JSON/jsonb cannot represent ({e})")
    except RecursionError as e:
        axis, detail = _classify_parse_failure(e)
        return None, axis, detail


def _iter_strings(value: Any):
    """A5.1's traversal: yield every string the parsed payload actually carries -- both object
    KEYS and VALUES, recursively through nested dicts/lists -- so `_representability_axis_failure`
    below can inspect ACTUAL CODEPOINTS rather than any particular serialization's escaped text.
    Numbers/booleans/None carry no string content and are skipped; they cannot carry a NUL or a
    surrogate codepoint in JSON's own value grammar."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from _iter_strings(k)
            yield from _iter_strings(v)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)


def _representability_failure_for_string(s: str) -> str | None:
    """A12: the representability RULE itself, factored out to ONE home (ADR-0012 P1) so it can
    be stated once and audited, rather than re-derived per call site. Postgres jsonb/text
    storage cannot store a literal U+0000 (NUL) character or an unpaired UTF-16 surrogate code
    point; both are checkable directly on `str.__iter__` because Python's `json.loads` already
    resolved every valid `\\uXXXX` escape (and every valid escaped surrogate PAIR combines into
    ONE composed, non-surrogate code point during decode -- a legitimate supplementary-plane
    character never leaves a lone surrogate character behind), so a lone surrogate CODE POINT
    appearing in a decoded `str` is, by construction, genuinely unpaired. Returns the failure
    detail (naming which of the two), or None if `s` is representable. Shared by
    `_representability_axis_failure` below (the write-payload scan, A4.1(b)/A5.1) and
    `_query_string_representability_failure` (the read-side query-parameter gate, A12) -- the
    SAME rule, never two."""
    if "\x00" in s:
        return ("contains a U+0000 (NUL) character, which Postgres jsonb text storage cannot "
                "represent")
    for ch in s:
        cp = ord(ch)
        if 0xD800 <= cp <= 0xDFFF:
            return (f"contains an unpaired UTF-16 surrogate character (U+{cp:04X}), which is "
                    f"not valid Unicode text and Postgres jsonb cannot store")
    return None


def _representability_axis_failure(payload: dict[str, Any]) -> str | None:
    """A4.1(b), FIXED per A5.1 (a regression in A4.1(b)'s own fix -- the first fix-introduced
    regression this spec's re-review loop found, per the spec's own framing). The PRE-A5 scan
    was denominated on an *escaped* serialization's text: a payload whose string content is the
    literal six characters "a backslash, then u0000" (documenting an escape in prose, a regex, a
    code snippet -- carrying NO NUL codepoint at all) re-escapes its OWN backslash when
    `json.dumps` runs, producing a longer escaped substring that happens to CONTAIN the same
    six characters the old scan matched on -- a false positive, refusing a payload jsonb stores
    fine, with a message asserting a NUL that was never there (the exact lying-signature class
    A4 exists to close, reproduced by A4's own fix; see this module's docstring, "A5 HARDENING"
    item 1).

    THE FIX: inspect the ACTUAL CODEPOINTS of the PARSED value, never any escaped/serialized
    text -- via `_representability_failure_for_string` above, the ONE home for the rule itself
    (A12 factored it out so a query-derived string could reuse it without re-deriving it).
    Walks every string AND every object key (`_iter_strings`); returns the failure detail, or
    None if the payload is representable."""
    for s in _iter_strings(payload):
        detail = _representability_failure_for_string(s)
        if detail is not None:
            return f"the payload {detail}"
    return None


def _query_string_representability_failure(name: str, value: str) -> JSONResponse | None:
    """A12: the rule, stated once (`_representability_failure_for_string`), audited at a second
    ingress -- EVERY string that crosses to psql argv, body-derived or query-derived, passes
    the SAME actual-codepoint representability closure before transport. `after_slug` is the
    only string-typed query/path parameter this service's route table declares (enumerated at
    A12's authoring; see the module docstring and serving/README.md) -- it carried the 512-byte
    length bound (A11) but not this representability gate at birth, so a literal NUL or an
    unpaired surrogate inside the 512-byte domain passed straight to `_psql`, where
    `subprocess.run` raised an uncaught `ValueError: embedded null byte` (a bare untyped 500,
    the exact shape §9 forbids). Returns the typed 422 (representability axis, A4.1(b)'s message
    family) naming `name` and the failure, or None when `value` is representable."""
    detail = _representability_failure_for_string(value)
    if detail is None:
        return None
    return JSONResponse(status_code=422, content={
        "detail": f"{name} {detail} (representability axis, spec A4.1(b)/A12)"})


def _bound_write_payload_ints(surface: str, payload: dict[str, Any]) -> JSONResponse | None:
    """A5.2: every integer-typed field the write payload CONTRACT declares -- the pydantic
    `*WriteIntFields` models in `boundary_models.py` are the enumeration authority, one per
    surface (see `WRITE_SURFACE_INT_FIELDS` above) -- is bounded `0 <= v <= MAX_ID` at the parse
    boundary, BEFORE psql's own bigint cast (which previously wore an honesty-losing 500
    `unclassified_failure` for an ordinary caller value that was simply too large -- see A5's
    §8 note on the sibling kernel defect this boundary fix stands beside, NOT fixes). Only a
    field the CALLER actually supplied is checked (an absent field is not this check's
    business); the bound is denominated on the *value*, not the Python type (A6 correction of
    A5.2's own residue: `isinstance(v, int)` let a JSON number in float/exponent form, e.g.
    `1e20`, skip the check and reach psql) -- any NUMERIC JSON value (`int` or `float`,
    `bool` excluded since it is `int`'s subclass but never an id) under one of these field
    names (or, for the one `bigint[]`-shaped field `enacts`, each element of a `list`) is
    bound-checked. A non-numeric JSON value under one of these field names is left for the
    kernel's own rowtype cast to judge (a type question, not a domain-bound question; this
    function adds no other semantic validation). An in-range float id (e.g. `5.0`) is NOT
    newly refused -- it passes through exactly as before. A8 item 2: finiteness is tested
    FIRST -- a NON-FINITE numeric value (Infinity/-Infinity/NaN) under a declared int field
    is NOT this check's business either; it is routed (by skipping) to A4.1(a)'s value-axis
    refusal downstream, so one condition wears one label (pre-A8, `Infinity` tripped the
    id-domain comparison and wore "got inf" while `NaN` correctly fell through to the value
    axis -- two labels split by IEEE-754 comparison accident). Returns the typed 422 naming
    the field and the bound, or None."""
    model = WRITE_SURFACE_INT_FIELDS.get(surface)
    if model is None:
        return None
    for field_name in model.model_fields:
        if field_name not in payload:
            continue
        value = payload[field_name]
        candidates = value if isinstance(value, list) else [value]
        for v in candidates:
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue  # a type mismatch here is the kernel's rowtype cast to judge, not ours
            # A8 item 2: FINITENESS FIRST. A non-finite numeric value (Infinity/-Infinity/NaN,
            # including a literal like 1e400 that json.loads silently parses to inf) is not an
            # out-of-DOMAIN id -- it is A4.1(a)'s value-axis class (jsonb cannot represent it
            # at all), and the pre-A8 code split one condition across two labels by IEEE-754
            # comparison accident (inf > MAX_ID tripped the id-domain message "got inf"; NaN
            # compared false everywhere and fell through to the value axis). Skipping here
            # routes EVERY non-finite value to A4.1(a)'s own check just downstream
            # (_reserialize_or_value_axis_failure, the message's ONE home per ADR-0012 P1) --
            # same typed 422, value axis, the label NaN already correctly wore.
            if isinstance(v, float) and not math.isfinite(v):
                continue
            # Mixed int/float comparison is exact in Python (no rounding to a float's nearest
            # representable value first) -- MAX_ID itself is not exactly representable as a
            # float, but `v > MAX_ID` still correctly refuses any float magnitude >= 2**63.
            if v < 0 or v > MAX_ID:
                return JSONResponse(status_code=422, content={
                    "detail": f"payload field '{field_name}' must satisfy 0 <= {field_name} <= "
                              f"{MAX_ID} (a Postgres bigint's own domain, spec A5.2/A6); got {v}"})
    return None


async def _read_bounded_body(request: Request) -> bytes:
    """A2.2 checkpoint (a): MAX_WRITE_BODY_BYTES enforced on the RAW request body, BEFORE any
    JSON parsing. Two sub-cases, both named in the spec: a Content-Length header, when the
    client sent one, is checked FIRST and refuses without ever reading the body (the 100 MB
    whole-body-buffered-then-parsed hazard A2.2 names, foreclosed before a single byte is
    read); a body with no (or a lying) Content-Length is bounded by reading it incrementally
    and aborting the instant the running total exceeds the bound -- never buffered whole first
    and measured after."""
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared = int(content_length)
        except ValueError:
            declared = None
        if declared is not None and declared > MAX_WRITE_BODY_BYTES:
            raise _BodyTooLarge(
                declared,
                f"the request's Content-Length ({declared} bytes) exceeds the "
                f"{MAX_WRITE_BODY_BYTES}-byte write bound (checkpoint a, before JSON parsing) "
                f"-- refused before reading the body.")
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > MAX_WRITE_BODY_BYTES:
            raise _BodyTooLarge(
                total,
                f"the request body exceeds the {MAX_WRITE_BODY_BYTES}-byte write bound "
                f"(checkpoint a, before JSON parsing) -- refused mid-read, never buffered "
                f"whole first.")
        chunks.append(chunk)
    return b"".join(chunks)


class _BodyReadTimeout(Exception):
    """A5.3: raised when the WHOLE body-read phase (`_read_bounded_body`'s stream loop, wrapped
    by `asyncio.wait_for` below) does not complete within `BODY_READ_TIMEOUT_S`. Distinct from
    `_BodyTooLarge` above (a SIZE refusal) and from `PsqlInfraFailure`'s time axis (which bounds
    the psql phase AFTER the body is already fully read) -- this is the body-READ phase's own
    bound, closing A5.3's finding that a trickled body (a client sending a declared-length body
    a few bytes at a time, never enough at once to trip the size bound) held the request open
    indefinitely. Caught once, by the app-level exception handler (`create_app`), and turned
    into the typed `body_read_timeout` 408 response -- same one-place-per-typed-shape discipline
    as `_BodyTooLarge`."""

    def __init__(self, timeout_s: float, message: str) -> None:
        super().__init__(message)
        self.timeout_s = timeout_s
        self.message = message


async def _bounded_raw_body(request: Request) -> bytes:
    """A3.1's plain-`def` write handlers, reconciled with the unavoidably-async ASGI body
    stream: FastAPI dependencies may be `async def` even when the path operation function they
    feed is a plain `def` -- the dependency runs on the event loop (where `await
    request.stream()` structurally must run; a stalled-network read on it is bounded by uvicorn/
    the client's own connection, not by this service's psql bounds), and the SYNCHRONOUS
    handler it feeds is then dispatched to FastAPI's threadpool, off the event loop -- exactly
    where the potentially-`PSQL_EXEC_TIMEOUT_S`-long psql call needs to run so a stalled write
    cannot starve `/health` (A3.1's amplifier finding). This is the smallest honest reading of
    "the write handlers become plain `def`": the handler -- the code that calls psql -- is
    plain `def`; the one line of genuinely-ASGI-bound I/O it depends on is factored out to where
    FastAPI's own async/sync split already provides for it, not reimplemented by hand.

    A5.3: the WHOLE read (`_read_bounded_body`, above -- Content-Length check plus the
    incremental stream loop) is now wrapped in `asyncio.wait_for(..., timeout=
    BODY_READ_TIMEOUT_S)`, bounding the body-read phase itself, independent of and prior to the
    psql-phase bounds (`PSQL_CONNECT_TIMEOUT_S`/`PSQL_EXEC_TIMEOUT_S`) that only start once the
    body is already fully in hand. A `_BodyTooLarge` raised INSIDE the wrapped call still
    propagates through `wait_for` unchanged (it only intercepts `asyncio.TimeoutError`, never
    swallows another exception) -- the size and time axes stay two independent gates, exactly
    like A2.2's own two size checkpoints."""
    try:
        return await asyncio.wait_for(_read_bounded_body(request), timeout=BODY_READ_TIMEOUT_S)
    except asyncio.TimeoutError as e:
        raise _BodyReadTimeout(
            BODY_READ_TIMEOUT_S,
            f"the request body was not fully received within BODY_READ_TIMEOUT_S="
            f"{BODY_READ_TIMEOUT_S}s (a stalled/trickled body-read phase, distinct from the "
            f"psql-phase time axis, spec A5.3) -- refused."
        ) from e


def create_app(cfg: BoundaryConfig) -> FastAPI:
    app = FastAPI(
        title="autoharn ledger boundary service",
        description="The outer declared Port into an autoharn-managed ledger "
                     "(design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md). Reads serve kernel "
                     "views verbatim; writes pass through the s43 boundary functions and "
                     "return the kernel's own write_verdict verbatim.",
        # A2.1: no self-documentation surface, disabled not merely unenumerated -- see this
        # module's docstring, "NO META-ROUTES". §9's route table is EXACTLY §3+§4's endpoints.
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    @app.exception_handler(PsqlInfraFailure)
    async def _infra_failure_handler(request: Request, exc: PsqlInfraFailure) -> JSONResponse:
        # A2.4, narrowed per A3.2, narrowed FURTHER per A4.3: the ONE place a genuinely
        # connection-level psql failure (exit 2 -- unreachable world, connection refusal -- or a
        # PSQL_EXEC_TIMEOUT_S stall -- the ONLY things that raise PsqlInfraFailure as of A4.3)
        # becomes a typed 503, for every route uniformly (ADR-0012 P1: one handler, not a
        # try/except duplicated per route). Registered on the DEDICATED exception class, never
        # the bare `RuntimeError` a foreign failure (RecursionError, for one) could also raise.
        _log_infra_failure(f"{request.method} {request.url.path}", exc)
        return infra_failure(
            "the ledger's underlying database connection failed -- this is an infrastructure "
            "problem, not a problem with your request; see the server's own log for full detail.")

    @app.exception_handler(PsqlUnclassifiedFailure)
    async def _unclassified_failure_handler(request: Request, exc: PsqlUnclassifiedFailure) -> JSONResponse:
        # A4.3: the ONE place a psql exit that is NEITHER exit 2 (connection-level) NOR a kernel
        # verdict -- exit 3 under ON_ERROR_STOP=1, or any other unrecognized nonzero residue --
        # becomes a typed 500. This is unreachable via an ordinary caller-supplied request after
        # A4.1's value closure and A4.2's id-domain closure, so its occurrence names a boundary
        # or deployment defect; the message says exactly that, honestly, rather than claiming
        # a cause (infra vs request) this boundary did not witness -- the lying-signature class
        # ADR-0002 rung 3 exists to forbid. Full psql stderr logged server-side only.
        _log_unclassified_failure(f"{request.method} {request.url.path}", exc)
        return unclassified_failure(
            "the storage layer refused for a reason this boundary did not anticipate -- this "
            "may be the deployment or the request; the boundary declines to guess. Full detail "
            "is logged server-side only; see the server's own log.")

    @app.exception_handler(KernelCallSaturated)
    async def _kernel_call_saturated_handler(request: Request, exc: KernelCallSaturated) -> JSONResponse:
        # A9: the ONE place saturation becomes a typed 503, for every route uniformly -- reads,
        # writes, and /health's own kernel probes alike, since every one of them reaches this
        # class only through `_psql`'s single shared admission gate (ADR-0012 P1: one handler,
        # not a try/except duplicated per call site). Deliberately NOT logged server-side (unlike
        # the infra/unclassified handlers above): saturation under load is an ordinary, expected,
        # caller-actionable condition, not a server-side anomaly worth a diagnostic line -- the
        # exception's own message already says everything the log would.
        return server_saturated(str(exc))

    @app.exception_handler(_BodyTooLarge)
    async def _body_too_large_handler(request: Request, exc: _BodyTooLarge) -> JSONResponse:
        # A2.2 checkpoint (a), re-homed here now that body-reading is a DEPENDENCY (async, so
        # it can await the ASGI body stream) rather than inline in the (now plain `def`, A3.1)
        # write handler -- a dependency's exception propagates to the app's own exception
        # handling before the handler is ever dispatched to the threadpool, so this is still
        # the ONE place checkpoint (a) becomes the typed 413 (ADR-0012 P1). A8: checkpoint
        # (a)'s bound is the raw-body/buffering one, and limit_bytes says so honestly.
        return payload_too_large(MAX_WRITE_BODY_BYTES, exc.observed_bytes, exc.message)

    @app.exception_handler(_BodyReadTimeout)
    async def _body_read_timeout_handler(request: Request, exc: _BodyReadTimeout) -> JSONResponse:
        # A5.3: the body-read phase's own time bound, symmetric with the body_too_large handler
        # directly above -- a dependency's exception propagates to the app's own exception
        # handling before the (now synchronous, off-the-event-loop) handler is ever dispatched.
        body = BodyReadTimeout(timeout_s=exc.timeout_s, message=exc.message)
        return JSONResponse(status_code=408, content=body.model_dump())

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            world=cfg.schema,
            service_principal=service_principal_name(cfg),
            capabilities=capability_manifest(cfg),
        )

    @app.get("/rows/current")
    def rows_current(after_id: int = 0, limit: int = 100) -> Response:
        if limit < 1 or limit > 1000:
            return JSONResponse(status_code=422, content={
                "detail": "limit must be between 1 and 1000 (transport-level bound, ADR-0002)"})
        # A4.2: after_id's domain closes symmetrically -- 0 <= after_id <= MAX_ID (the A2.6
        # lower-bound precedent, completed upward).
        oor = _out_of_range_id("after_id", after_id)
        if oor is not None:
            return oor
        rows = _query_json(
            cfg,
            f"SELECT coalesce(jsonb_agg(t ORDER BY t.id), '[]'::jsonb) FROM "
            f"(SELECT * FROM {cfg.schema}.ledger_current WHERE id > {after_id} "
            f"ORDER BY id LIMIT {limit}) t;",
        )
        return JSONResponse(content=rows)

    @app.get("/rows/{row_id}")
    def row_by_id(row_id: int) -> Response:
        # A4.2: the path-parameter id domain -- 0 <= row_id <= MAX_ID, typed 422 outside it,
        # BEFORE this value ever reaches psql's bigint cast (which previously wore a 503 it did
        # not earn on an over-range id).
        oor = _out_of_range_id("row_id", row_id)
        if oor is not None:
            return oor
        row = _query_json(
            cfg, f"SELECT to_jsonb(t) FROM (SELECT * FROM {cfg.schema}.ledger WHERE id = {row_id}) t;")
        if row is None:
            return JSONResponse(status_code=404, content={"detail": f"no row {row_id}"})
        return JSONResponse(content=row)

    @app.get("/rows/{row_id}/history")
    def row_history(row_id: int, after_id: int = 0, limit: int = HISTORY_DEFAULT_LIMIT) -> Response:
        # A4.2: same id-domain closure as row_by_id above (the path parameter).
        oor = _out_of_range_id("row_id", row_id)
        if oor is not None:
            return oor
        # A11 item 2: the LEADING existence check -- before pagination is even validated, and
        # before the recursive CTE below ever runs. Pre-A11 this route answered `200 []` for a
        # nonexistent id, where the sibling GET /rows/{id} typed-404s the identical input class;
        # the empty array was only an INFERRED nonexistence signal (an existing row always
        # contributes at least its own hop, so "no hops" and "no such row" happened to coincide
        # for a real row's history, but a caller had to trust that inference rather than being
        # told). `_row_not_found` (ADR-0012 P1, named once, shared with row_by_id's own 404
        # shape) settles existence FIRST; a nonexistent in-domain id gets the sibling route's
        # EXACT typed 404, and the CTE below never runs for it.
        not_found = _row_not_found(cfg, row_id)
        if not_found is not None:
            return not_found
        # A10: the SAME `1 <= limit <= 1000` / `after_id >= 0` discipline as the four A5.4
        # routes -- same constants, same message family (checked in the SAME order
        # /rows/current uses: limit first, then after_id's own id-domain closure). Default
        # limit is HISTORY_DEFAULT_LIMIT (1000, not the other routes' 100) -- see that
        # constant's own docstring for why: a short chain (the overwhelmingly common case)
        # must come back byte-identical to the pre-A10 unpaginated response with NO query
        # parameters supplied at all, and a 100-row default would silently truncate any
        # chain longer than that where the pre-A10 behavior never did.
        if limit < 1 or limit > 1000:
            return JSONResponse(status_code=422, content={
                "detail": "limit must be between 1 and 1000 (transport-level bound, ADR-0002)"})
        oor = _out_of_range_id("after_id", after_id)
        if oor is not None:
            return oor
        # The full supersession chain both directions (predecessors this row's lineage
        # superseded, and any successor that superseded it), each hop annotated with its own
        # superseding row id -- spec §3's "each hop WITH its superseding row id". A10: the
        # chain is computed in full (the CTE below is unchanged from pre-A10), then PAGED in
        # an outer query by the hop's OWN row id (`l.id > after_id ORDER BY l.id LIMIT limit`,
        # the same id-keyed cursor shape /rows/current already uses) -- every hop remains
        # reachable across pages by walking after_id forward, and each row's own
        # 'superseded_by' expression is UNCHANGED from the pre-A10 query, so a page that
        # happens to contain every hop of a short chain is byte-identical to the old
        # unpaginated response (same envelope, same per-row field set and order).
        rows = _query_json(
            cfg,
            f"WITH RECURSIVE chain(id) AS ("
            f"  SELECT {row_id}::bigint"
            f"  UNION"
            f"  SELECT l.id FROM {cfg.schema}.ledger l JOIN chain c ON l.id = c.id"
            f"),"
            f"chain_up AS ("
            f"  SELECT id FROM chain"
            f"  UNION"
            f"  SELECT l.supersedes FROM {cfg.schema}.ledger l JOIN chain_up c ON l.id = c.id "
            f"    WHERE l.supersedes IS NOT NULL"
            f"),"
            f"chain_full(id) AS ("
            f"  SELECT id FROM chain_up"
            f"  UNION"
            f"  SELECT l.id FROM {cfg.schema}.ledger l JOIN chain_full c "
            f"    ON l.supersedes = c.id"
            f")"
            f"SELECT coalesce(jsonb_agg(t.row ORDER BY t.id), '[]'::jsonb) FROM ("
            f"  SELECT l.id AS id, to_jsonb(l) || jsonb_build_object("
            f"    'superseded_by', (SELECT s.id FROM {cfg.schema}.ledger s "
            f"                      WHERE s.supersedes = l.id)) AS row "
            f"  FROM {cfg.schema}.ledger l WHERE l.id IN (SELECT id FROM chain_full) "
            f"    AND l.id > {after_id} "
            f"  ORDER BY l.id LIMIT {limit}"
            f") t;",
        )
        return JSONResponse(content=rows)

    @app.get("/credited")
    def credited(after_id: int = 0, limit: int = 100) -> Response:
        if not _regclass_exists(cfg, f"{cfg.schema}.credited_current"):
            return capability_absent(
                "s44-credited-view",
                "This world carries no credited_current view (kernel/lineage/s44, unbuilt as "
                "of this service's authoring -- design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md "
                "§7). The service refuses to fall back to ledger_current for this endpoint "
                "(that would be the vacuous-pass F49 class, silently serving a weaker "
                "reading under the credited-only contract's name); use GET /rows/current "
                "until this world's kernel gains the view.")
        if limit < 1 or limit > 1000:
            return JSONResponse(status_code=422, content={"detail": "limit must be between 1 and 1000"})
        # A4.2: same id-domain closure as /rows/current's after_id.
        oor = _out_of_range_id("after_id", after_id)
        if oor is not None:
            return oor
        rows = _query_json(
            cfg,
            f"SELECT coalesce(jsonb_agg(t ORDER BY t.id), '[]'::jsonb) FROM "
            f"(SELECT * FROM {cfg.schema}.credited_current WHERE id > {after_id} "
            f"ORDER BY id LIMIT {limit}) t;",
        )
        return JSONResponse(content=rows)

    @app.get("/standing/principals")
    def standing_principals(after_id: int = 0, limit: int = 100) -> Response:
        if not _regclass_exists(cfg, f"{cfg.schema}.principal_relations"):
            return capability_absent(
                "s41-identity",
                "This world carries no principal-identity/relation views "
                "(kernel/lineage/s41-principal-bindings-and-relations.sql) -- "
                "GET /standing/principals is refused rather than served from a view this "
                "world's kernel does not have.")
        # A5.4: the SAME `limit`/`after_id` discipline as /rows/current -- `principal_standing_
        # current` carries `id` (the view's own `p.id`), so this is a plain id-ordered page,
        # identical in shape to /rows/current's own query.
        if limit < 1 or limit > 1000:
            return JSONResponse(status_code=422, content={
                "detail": "limit must be between 1 and 1000 (transport-level bound, ADR-0002)"})
        oor = _out_of_range_id("after_id", after_id)
        if oor is not None:
            return oor
        rows = _query_json(
            cfg,
            f"SELECT coalesce(jsonb_agg(t ORDER BY t.id), '[]'::jsonb) FROM "
            f"(SELECT * FROM {cfg.schema}.principal_standing_current WHERE id > {after_id} "
            f"ORDER BY id LIMIT {limit}) t;",
        )
        return JSONResponse(content=rows)

    @app.get("/work/items")
    def work_items(after_slug: str = "", limit: int = 100, after_id: int | None = None) -> Response:
        if not _regclass_exists(cfg, f"{cfg.schema}.work_item_current"):
            return capability_absent(
                "s22-work",
                "This world carries no work-item views (kernel/lineage/s22-work-item-ledger"
                ".sql) -- GET /work/items is refused rather than served from a view this "
                "world's kernel does not have.")
        # A11 item 1: `after_id` (the pre-A11 `row_number() OVER (ORDER BY slug)` synthetic
        # ordinal cursor) is RETIRED on this route -- it was recomputed PER REQUEST, so an item
        # inserted mid-walk with a slug sorting before an already-served item shifted every
        # ordinal after it (witnessed: pages [aa,cc] then [cc,ee] served against a view reading
        # [aa,bb,cc,ee,gg] -- cc served twice, bb never). The cursor re-keys to the view's OWN
        # TRUE key: `after_slug` (keyset `WHERE slug > :after_slug ORDER BY slug`) -- a served
        # slug can never be re-served (the cursor is a VALUE, not a POSITION), so this route's
        # walk is duplicate-free by construction. Disclosed, named residual (spec A11, not a
        # silent gap): a row inserted BEHIND an in-flight cursor is not visible to THAT walk --
        # no snapshot-free scheme over a non-append-monotonic key (slugs, unlike ledger ids, are
        # not append-monotonic) can promise otherwise -- it simply joins the NEXT walk. A
        # supplied `after_id` on THIS route is never silently ignored (A10's own lesson, applied
        # here too): it refuses, typed, teaching `after_slug` instead of guessing the caller's
        # intent or quietly serving a different page shape than requested.
        if after_id is not None:
            return JSONResponse(status_code=422, content={
                "detail": f"after_id is not accepted on GET /work/items -- this route pages on "
                          f"after_slug (the view's own natural key, spec A11), never a "
                          f"synthetic ordinal; got after_id={after_id}, resupply as "
                          f"after_slug=<last-served-slug> instead"})
        if limit < 1 or limit > 1000:
            return JSONResponse(status_code=422, content={
                "detail": "limit must be between 1 and 1000 (transport-level bound, ADR-0002)"})
        # A11: `after_slug`'s own domain -- byte-length <= MAX_AFTER_SLUG_BYTES, typed 422
        # beyond it; ANY in-domain value is a valid cursor position (keyset semantics need no
        # existence check -- unlike an id cursor, a slug that names no row simply starts the
        # walk at the first slug greater than it, which is well-defined regardless of whether
        # that exact slug was ever opened).
        after_slug_bytes = len(after_slug.encode("utf-8"))
        if after_slug_bytes > MAX_AFTER_SLUG_BYTES:
            return JSONResponse(status_code=422, content={
                "detail": f"after_slug must be at most {MAX_AFTER_SLUG_BYTES} bytes (a slug "
                          f"over this bound names no real item any world this kernel scaffolds "
                          f"could ever open, spec A11); got {after_slug_bytes} bytes"})
        # A12: the representability closure, generalized off the write-payload's dict shape onto
        # THIS bare query-parameter string -- a literal U+0000 or an unpaired UTF-16 surrogate
        # inside the 512-byte domain above still reached `_psql` unchecked pre-A12, where
        # `subprocess.run` raised an uncaught `ValueError: embedded null byte` (a bare untyped
        # 500). Checked after the length bound (the cheaper, purely-local check first) and
        # before the value ever crosses to psql's `-v` argument below.
        repr_oor = _query_string_representability_failure("after_slug", after_slug)
        if repr_oor is not None:
            return repr_oor
        # The slug crosses to psql as a BOUND `-v` argument (`:'after_slug'`), never spliced as
        # SQL text -- the same injection-safe substitution the write routes already use for
        # payload bodies (spec A11: "pass to psql as bound arguments through the existing
        # transport exactly like other string params -- no interpolation").
        rows = _query_json(
            cfg,
            f"SELECT coalesce(jsonb_agg(t ORDER BY t.slug), '[]'::jsonb) FROM "
            f"(SELECT * FROM {cfg.schema}.work_item_current WHERE slug > :'after_slug' "
            f"ORDER BY slug LIMIT {limit}) t;",
            extra_v={"after_slug": after_slug},
        )
        return JSONResponse(content=rows)

    def make_write_route(surface: str, fn: str):
        # A3.1: plain `def`, not `async def` -- FastAPI/Starlette dispatches a plain `def` path
        # operation function to its threadpool, off the event loop, so this handler's psql
        # calls (each now bounded by PSQL_CONNECT_TIMEOUT_S/PSQL_EXEC_TIMEOUT_S, but still a
        # blocking subprocess.run for up to that long) never starve `/health` or any other
        # route the way calling them directly from an `async def` handler on the event loop
        # would (matching the read routes, which were already plain `def`). The one piece of
        # genuinely-ASGI-bound I/O -- reading the raw request body -- is factored out to the
        # `_bounded_raw_body` async dependency (see its own docstring), which FastAPI awaits on
        # the event loop BEFORE dispatching this synchronous handler to the threadpool.
        def handler(request: Request, raw_body: bytes = Depends(_bounded_raw_body)) -> Response:
            if not bool(_query_json(
                cfg,
                f"SELECT to_jsonb(EXISTS (SELECT 1 FROM pg_proc p JOIN pg_namespace n "
                f"ON n.oid = p.pronamespace WHERE n.nspname = '{cfg.kern}' "
                f"AND p.proname = '{fn}' AND p.prosecdef));",
            )):
                return capability_absent(
                    "s43-boundary",
                    f"This world carries no s43 write boundary (kernel.{fn} absent) -- "
                    f"POST /write/{surface} refuses entirely rather than falling back to a "
                    f"raw INSERT (design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md §4: 'the "
                    f"service NEVER falls back to raw INSERT; there is no code path that "
                    f"writes SQL DML').")

            # A3.2 parse closure: `json.loads` on `bytes` decodes internally, so this ONE
            # explicit call's `except` clause is where ALL three A3.2 axes are caught --
            # encoding (UnicodeDecodeError, a ValueError subclass), value magnitude (an
            # oversized integer literal, ValueError), and structure (JSONDecodeError, also
            # ValueError; or RecursionError on deep nesting, which subclasses RuntimeError --
            # exactly why the app's infra handler is narrowed to PsqlInfraFailure and cannot
            # accidentally swallow this). Never echoes raw_body back to the client.
            try:
                payload = json.loads(raw_body) if raw_body else None
            except (ValueError, RecursionError) as e:
                axis, detail = _classify_parse_failure(e)
                return JSONResponse(status_code=422, content={
                    "detail": f"malformed write payload -- {axis} axis: {detail}"})
            if not isinstance(payload, dict):
                return JSONResponse(status_code=422, content={
                    "detail": "write payload must be a JSON object (transport-level shape check, spec §4)"})

            # A5.2: the write-body id-domain closure -- every integer-typed field this
            # surface's payload contract declares (boundary_models.py's *WriteIntFields models)
            # is bounded 0 <= v <= MAX_ID, BEFORE psql's own bigint cast ever sees it.
            int_field_oor = _bound_write_payload_ints(surface, payload)
            if int_field_oor is not None:
                return int_field_oor

            # A4.1(a): value closure -- non-finite numbers. This SAME re-serialization is also
            # A2.2 checkpoint (b)'s size measurement and the exact text that crosses to psql
            # below -- one call, one home (ADR-0012 P1), not a separate throwaway dumps just for
            # this check. `allow_nan=False` refuses Infinity/NaN/1e400-magnitude values on the
            # value axis before they ever reach jsonb, which has no representation for them.
            # A13: this call also carries its OWN structure-axis refusal (the dumps-side
            # recursion net) -- `reser_axis` names which axis fired (`"value"` or
            # `"structure"`), so the typed 422 below labels correctly either way, never
            # mislabeling A13's structure-axis refusal as this checkpoint's value axis.
            payload_json, reser_axis, reser_detail = _reserialize_or_value_axis_failure(payload)
            if payload_json is None:
                return JSONResponse(status_code=422, content={
                    "detail": f"malformed write payload -- {reser_axis} axis: {reser_detail}"})

            # A4.1(b): value closure -- Postgres-text-representability (U+0000 / an unpaired
            # UTF-16 surrogate; see _representability_axis_failure's own docstring for why this
            # needs its own, separately-moded serialization rather than reusing payload_json
            # above). A7: this scan's own traversal (_iter_strings) is recursive and inherits
            # none of A3.2's parse-time recursion-depth protection -- a well-formed body nested
            # deeply enough (under every size/structure bound already checked above) overflows
            # HERE, after parse, rather than inside json.loads. Caught the same way A3.2 catches
            # it -- same classifier, same typed-422 shape, same structure axis -- because to the
            # caller this is observably the same "body nests too deeply" class, just a different
            # Python frame overflowing first.
            try:
                repr_detail = _representability_axis_failure(payload)
            except RecursionError as e:
                axis, detail = _classify_parse_failure(e)
                return JSONResponse(status_code=422, content={
                    "detail": f"malformed write payload -- {axis} axis: {detail}"})
            if repr_detail is not None:
                return JSONResponse(status_code=422, content={
                    "detail": f"malformed write payload -- representability axis: {repr_detail}"})

            # A2.2 checkpoint (b), RE-DENOMINATED per A8 item 1(i): the re-serialized payload,
            # bounded BEFORE the psql subprocess against MAX_PSQL_ARG_BYTES -- the transport's
            # TRUE per-argument capacity (the payload crosses as ONE psql `-v` argument;
            # Linux's per-argument wall is MAX_ARG_STRLEN = 131 072 bytes, not the 2 MiB
            # total-argv ARG_MAX the pre-A8 bound was sized against). A payload can pass
            # checkpoint (a) and still fail here: any raw body between the two bounds (W25),
            # or non-ASCII content that json.dumps's default ensure_ascii=True escaping
            # expands past its raw UTF-8 byte count (W9).
            observed = len(payload_json.encode("utf-8"))
            if observed > MAX_PSQL_ARG_BYTES:
                return payload_too_large(
                    MAX_PSQL_ARG_BYTES,
                    observed,
                    f"the JSON payload, re-serialized, is {observed} bytes -- exceeds the "
                    f"{MAX_PSQL_ARG_BYTES}-byte transport bound (checkpoint b, before the "
                    f"psql subprocess: the payload crosses as ONE psql argument, and the "
                    f"kernel's per-argument transport wall, MAX_ARG_STRLEN, is 131072 bytes "
                    f"-- this bound sits under it with margin, spec A8).")

            verdict = _query_json(
                cfg,
                f"SELECT to_jsonb(v) FROM {cfg.kern}.{fn}(:'payload'::jsonb) v;",
                extra_v={"payload": payload_json},
            )
            # Kernel verdicts (accepted AND refused) cross byte-verbatim as HTTP 200 -- a
            # kernel refusal is a first-class domain RESULT, not a transport error (spec §4).
            return JSONResponse(status_code=200, content=verdict)
        handler.__name__ = f"write_{surface}"
        return handler

    for surface, fn in WRITE_SURFACES.items():
        app.add_api_route(f"/write/{surface}", make_write_route(surface, fn), methods=["POST"])

    return app


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python3 -m serving.boundary_service",
        description="The FastAPI outer boundary into an autoharn-managed ledger "
                     "(design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md).")
    p.add_argument("--deployment", required=True,
                    help="path to this project's deployment.json (the SAME record led/judge read)")
    p.add_argument("--host", default="127.0.0.1",
                    help="bind address for THIS HTTP service (default 127.0.0.1, loopback-only)")
    p.add_argument("--port", type=int, default=8420)
    p.add_argument("--i-understand-this-exposes-the-ledger", action="store_true",
                    help="required to bind any non-loopback address -- the ledger carries "
                         "operator-real content (spec §2, the OTel-collector localhost-only posture)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    if args.host not in _LOOPBACK_HOSTS and not args.i_understand_this_exposes_the_ledger:
        sys.stderr.write(
            f"boundary_service: REFUSED -- --host {args.host!r} is not a loopback address "
            f"({sorted(_LOOPBACK_HOSTS)}). The ledger carries operator-real content; binding "
            f"it to a non-loopback interface is refused unless you pass "
            f"--i-understand-this-exposes-the-ledger explicitly (design/"
            f"FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md §2; construction-time refusal, ADR-0002 "
            f"rung 1 -- the anomaly never reaches a bound socket).\n")
        return 2
    record = deployment_record.load_deployment(args.deployment)
    cfg = BoundaryConfig(record)
    app = create_app(cfg)
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
