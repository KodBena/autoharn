#!/usr/bin/env python3
"""boundary_service -- the FastAPI outer boundary Port into an autoharn-managed ledger
(design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md, the RATIFIED build basis; ledger rows 1471,
1481, 1518; orchlog.d/panel-single-boundary-direction.md; kernel/lineage/
s43-typed-verdict-write-boundary.sql; law/adr/0002, 0012 P2, 0016).

MULTIPLEXING (design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md, maintainer-ratified
2026-07-18, ledger decision row 1631): as of this build, ONE process serves N deployments,
selected by a mandatory leading `/d/{deployment}` path segment -- no per-deployment server
processes, no unprefixed-route mode (a single-deployment config is the degenerate, expected
common case, and the discriminator is still mandatory for it). `--config <path>` names a TOML
file (`serving/boundary_multiplex_config.py`, the one home for its shape); the WHOLE file
validates -- unknown key, missing key, or zero deployments -- before the socket ever binds
(spec §3). Every A1-A13 closure axis above holds identically per resolved deployment (spec
§4); `MAX_INFLIGHT_KERNEL_CALLS` stays the GLOBAL admission bound (it protects the shared
threadpool, process-wide), and gains a per-deployment sub-bound
(`MAX_INFLIGHT_PER_DEPLOYMENT`, `compute_per_deployment_limit`, computed and printed at
startup) so one deployment's stalled kernel cannot occupy the whole global bound and starve
its siblings -- both saturation refusals are typed 503 under DISTINCT labels
(`server_saturated` vs `deployment_saturated`, one condition per label, the A6/A8 label-honesty
ruling extended to the new axis). An unrecognized `{deployment}` segment is a typed 404
`unknown_deployment` naming the full known set.

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
turned into one typed 422 that names WHICH axis failed (encoding / value / structure)
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

READ-SURFACE AMENDMENT (design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md, ratified ledger decision row
1652): the route table grows from eleven to FOURTEEN -- `GET /d/{deployment}/views/{view}` (the
closed-allowlist derived-read carrier, `VIEW_REGISTRY`), `GET /d/{deployment}/rows/asof/{ts}` (the
as-of reconstruction), `GET /d/{deployment}/meta` (the capability surface). A12's own string-typed-
parameter enumeration above is re-run at this new count, not silently left stale: `views_view`
gains a SECOND `after_slug` site (identical gate, `_query_string_representability_failure`, same
call) for the view registry's own text-keyed entries; `rows_asof`'s `ts` path parameter is
DELIBERATELY NOT run through the same gate -- a string that survives `datetime.fromisoformat`
cannot carry a U+0000 or an unpaired surrogate (ISO-8601's character class structurally excludes
both), so the gate would be dead code there, not a second layer of defense (see `rows_asof`'s own
comment). The A8 `OSError`/A12 `ValueError` choke-point net in `_psql` still covers every site
uniformly regardless of this reasoning being right.

THE DUMPS-SIDE RECURSION NET (spec A13, post-fixpoint microamendment, ledger row 1621). Not a
finding -- `_reserialize_or_value_axis_failure`'s own `json.dumps` call had no `RecursionError`
handling of its own and was protected only by the accident that `json.loads` overflows at the
same-or-shallower depth on this CPython build; no caller input reaches it today. Designed
safety now replaces that accidental safety: the call gains `except RecursionError`, joining the
SAME typed 422 structure-axis refusal A7 already gave the adjacent post-parse traversal -- one
clause, same message family, no behavior change for any input that parses today.

ONE GUARDED-TRAVERSAL HELPER, NOT THREE INDEPENDENT NETS (ledger row 1628 / work item
boundary-recursion-net-single-invariant, re-asserted from autoharn1, filed against A13's own
independent out-of-frame review). A3.2, A13, and A7 above each added their OWN
`except RecursionError` clause -- three independently-authored except clauses sharing only the
`_classify_parse_failure` classifier by convention, not by any structural guarantee. Nothing
stopped a fourth deep-walk site (a payload traversal added later) from being written without
routing through that classifier, or from open-coding its own bypassing `except RecursionError`.
`_guard_recursion` below is now the ONE home every deep-walk call site in this module routes
through -- `json.loads` (A3.2, both write routes), `json.dumps(..., allow_nan=False)` (A13), and
`_representability_axis_failure`'s `_iter_strings` walk (A7, both write routes) all call through
it rather than opening their own `except RecursionError`. `gates/deep_walk_recursion_guard.py`
enforces this mechanically: it refuses any `except ... RecursionError ...` clause in this file
OUTSIDE `_guard_recursion`'s own body, so a fourth site that bypasses the helper is caught at
gate time, not left to review discipline alone. Same behavior for every input that already
classified correctly (A3.2/A13/A7's own three sites), by construction -- the classifier itself
(`_classify_parse_failure`) is unchanged, only WHERE it is reached from is unified.

AXIS-LABEL VOCABULARY, UNIFIED (same ledger item's second residual): `_classify_parse_failure`'s
oversized-integer-literal leg used to return the axis name `"value magnitude"`, while the
non-finite-number check (`_reserialize_or_value_axis_failure`, A4.1(a)) and every other value-ish
refusal in this module use the single word `"value"` (matching the sibling one-word axis names
`"encoding"`/`"structure"`/`"representability"`, and the extensively-fixture-covered "value axis"
phrasing README.md and seen-red/boundary-service/run_fixtures.py already use for W15/W26). Two
spellings for one conceptual axis, sitting beside genuinely new code, is exactly the kind of
inconsistency ADR-0012's "one vocabulary, one home" spirit flags -- `"value magnitude"` is
retired; the oversized-integer leg now also reports axis `"value"`. No consumer distinguished the
two spellings before this (the client-visible DETAIL text, not the axis label, already carried
the specific "too large to parse" wording) -- the only visible change is the axis word itself.

DIAGNOSTIC-GRADE JSON-LINES LOGGING (design/FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md, RATIFIED
IN FULL 2026-07-27, ledger row 1500). `boundary_diagnostic_log.py` is the ONE home (ADR-0012
P1) for a per-request context object (L1, minted by this module's own async `@app.middleware
("http")` -- NEVER a plain-`def` dependency, per the row-1498 witness that a plain-`def`
dependency's OWN `ContextVar.set()` from inside Starlette's threadpool never flows back), a
closed eight-event vocabulary with a per-event required-field contract raised loudly BEFORE any
level filter (L2), and one JSON-line rendering to this service's EXISTING stderr/service.log
capture -- no new destination, no new rotation, no new config channel beyond one optional
`log_level` key in the already-existing multiplex TOML (L3). `_log_infra_failure`/
`_log_unclassified_failure`/the startup banner below are the three pre-existing call sites this
build migrates to typed events, beside their existing human stderr lines, never instead of them
(L4). This layer is DIAGNOSTIC-grade ONLY -- no fact here is evidentiary; a request's outcome is
never decided by whether a log line was written (see `boundary_diagnostic_log.py`'s own
docstring for the full design, the fail-loud/never-500-a-request tension and its resolution,
and the exact reasoning for why L1 must be async middleware).

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import is top-of-file.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import copy
import datetime
import hashlib
import json
import math
import os
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

import uvicorn
import uvicorn.config
from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

# Path setup, NOT lazy imports (both `sys.path.insert` calls execute at module import time,
# unconditionally, before either import below runs -- the gate that actually arbitrates this,
# gates/no_lazy_imports.py, passes on this file). Both inserts are needed regardless of HOW
# this module is invoked: `python3 -m serving.boundary_service` (spec §2's launch command)
# puts the REPO ROOT on sys.path[0], not serving/ itself, so the sibling import below
# (`boundary_models`, a top-level import for house-convention consistency with every other
# filing/ consumer, not a package-relative one) needs its own directory added explicitly.
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "filing"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bootstrap"))
import deployment_record  # filing/deployment_record.py -- the ONE home for the deployment.json shape  # noqa: E402
# serving/ensure_running.py's own `pid_is_boundary_service` -- the ONE identity check `autoharn
# service stop` and ensure_running.py's own pre-spawn pidfile check both already use (ADR-0012
# P1) -- reused here (round-4 review SEVERE-B item 1) so this module's own stale-pidfile-squat
# reclaim asks the exact SAME question, never a second, drifting copy of the same logic. No
# import cycle: ensure_running.py imports boundary_cli_client, never this module.
import ensure_running  # noqa: E402

import boundary_multiplex_config  # noqa: E402  (design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md §3)
# design/FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md (RATIFIED, ledger row 1500): the ONE home for
# this service's diagnostic JSON-lines log -- L1's RequestContext/ContextVar, L2's closed event
# vocabulary + contract validation, L3's JSON-line rendering. See that module's own docstring
# for the full design and the witnessed contextvars-through-threadpool constraint it is built
# around (ledger row 1498).
import boundary_diagnostic_log  # noqa: E402
# design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md's /meta route reuses bootstrap/migrate_core.py's OWN
# manifest derivation (`_manifest`, a directory read over kernel/lineage/ via bootstrap/
# lineage_manifest.py, no DB call) as the ONE home for "what is the ordered kernel/lineage/*.sql
# birth chain" (ADR-0012 P1) -- see `_lineage_head`
# below for why the DB-touching half of migrate_core's own head-detection is deliberately NOT
# reused (it would reopen an unbounded, non-admission-gated psql call inside this otherwise fully
# disciplined service).
import migrate_core  # noqa: E402  (bootstrap/migrate_core.py)
# serving/bounds.py -- the ONE home (ADR-0012 P1) for the service layer's bound vocabulary; every
# constant below was formerly declared locally in this module (a pure relocation, ledger row 1514
# item 2). gates/bounds_kernel_drift.py is the cross-layer mechanism keeping the two kernel-tied
# names (IDENTITY_HEADER_MAX_BYTES, MAX_WRITE_BODY_BYTES) from silently drifting off their kernel
# CHECK twins.
from bounds import (  # noqa: E402
    IDENTITY_HEADER_MAX_BYTES,
    MAX_AFTER_SLUG_BYTES,
    MAX_ARTIFACT_BODY_BYTES,
    MAX_PSQL_ARG_BYTES,
    MAX_WRITE_BODY_BYTES,
)
from boundary_models import (  # noqa: E402
    AnonymousWriteRefused,
    ArtifactWriteIntFields,
    AttestationResponse,
    BankedDoctorSummary,
    BankedJudgeVerdict,
    BankedVerifyChainVerdict,
    BodyReadTimeout,
    CapabilityAbsent,
    CapabilityManifest,
    DeploymentSaturated,
    HealthResponse,
    IdentityHeaderInvalid,
    InfraFailure,
    KindsResponse,
    LedgerWriteIntFields,
    MetaResponse,
    MintedActorConflict,
    MissiveDisposeWriteIntFields,
    NoBankedArtifact,
    ObligationRevokeWriteIntFields,
    ObligationWriteIntFields,
    PayloadTooLarge,
    RegistrationWriteIntFields,
    ReviewWriteIntFields,
    ServerSaturated,
    SseSaturated,
    UnclassifiedFailure,
    UnknownDeployment,
    UnknownView,
)

# design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md, ratified ledger decision row 1652: this service's
# own declared version -- bumped from the implied pre-amendment "1.0.0" (eleven routes) to name
# the fourteen-route closure. A SERVICE-owned fact (never a kernel fact); reported verbatim by
# GET /meta. Bumped AGAIN to 1.2.0 by design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part A+B (ledger
# row 1150): three new routes (POST /write/obligation_revoke via the existing WRITE_SURFACES
# table -- no route-table growth of its own kind, just a new dict entry; GET /artifacts/{hash},
# GET /artifacts/{hash}/stat, POST /artifacts -- genuinely new route SHAPES, unlike
# VIEW_REGISTRY's own registry-only growths, which this version deliberately does NOT track).
# Bumped AGAIN to 1.3.0 for TWO route-shape additions this build found sitting on top of each
# other, both fixed here rather than only the one this commission named (CLAUDE.md's hazard-in-
# reach rule -- this exact version comment and the route table below were already being touched):
# (a) design/FABLE-MISSIVES-KERNEL-SPEC.md's `POST /write/missive_dispose` (kernel/lineage/
# s58-missive-substrate.sql, ledger row 1263) shipped wired into WRITE_SURFACES but this version
# literal, this comment, and `seen-red/boundary-service/run_fixtures.py`'s own W12 EXPECTED_ROUTES
# were never updated for it -- a real, pre-existing doc/fixture drift, not touched by this
# route's own build, found and closed here since this build already has this exact file, this
# exact comment block, and that exact fixture's EXPECTED_ROUTES set open; (b) `GET
# /d/{deployment}/kinds` (ledger row 1480: the maintainer's ruling restoring the legacy direct-
# psql `led`'s dropped valid-kinds TEACHING on the SERVED transport, this commission) -- a
# genuinely new route SHAPE, not a VIEW_REGISTRY-style registry growth (see `KindsResponse`'s own
# docstring in boundary_models.py for why this earns a dedicated route rather than a `/meta`
# field or a VIEW_REGISTRY entry).
# Bumped AGAIN to 1.4.0 (ledger rows 153/154, experience4 panel requests, missive receipt row
# 149): TWO changes, one of each already-established kind, not a third new kind. (a) FIVE new
# VIEW_REGISTRY members (work_edge_blocks_close, discharging_attest, work_violation_history,
# work_bookkeeping_closes, countersigned_in_force) -- registry-only growth, which per the note
# just above this version deliberately does NOT track; named here only for completeness of this
# comment's own history, the version arithmetic below does not count it. (b) `GET
# /d/{deployment}/rows/current` gains ONE new, strictly-typed, opt-in query parameter,
# `include_superseded` -- the DEFAULT-omitted response is BYTE-IDENTICAL to 1.3.0 (same query,
# same shape, no new field), so this is not a route-table growth of the (a)/(b)/(kinds) kind
# above either; it earns the bump anyway because it is a genuine, new, documented capability on
# an EXISTING route's response contract (a caller who opts in sees a new `is_current` field per
# row) -- silently leaving the version literal at 1.3.0 while the served contract grew would be
# the version-drift bug this file's own history (the 1.3.0 note, item (a)) was already once
# caught missing.
BOUNDARY_SERVICE_VERSION = "1.7.0"
# Bumped to 1.5.0 (design/FABLE-BOUNDARY-SSE-EVENTS-SPEC.md, maintainer pre-ratified, work item
# boundary-sse-events, ledger row 169): ONE new route SHAPE, `GET /d/{deployment}/events`
# (text/event-stream, head-advancement-only) -- a genuinely new route shape, the same (a)/(b)/
# (kinds) kind of growth the notes above already earn a bump for, not a registry-only growth.
# `/meta` also gains two new, strictly additive fields (`max_sse_clients`/
# `sse_poll_interval_secs`) -- additive alone would not need the bump (the 1.4.0(b) note above),
# but the new route already does. `HealthResponse`/`MetaResponse`'s own `protocol_version`
# (WIRE_PROTOCOL_VERSION) is UNCHANGED -- an additive /meta field, and an entirely-opt-in new
# route an existing client never calls, does not make an existing client misparse anything
# (boundary_models.py's own protocol_version bump rule, verbatim).
# Bumped to 1.6.0 (work item boundary-capability-manifest, ledger row 173): NO new route -- this
# is the additive-field-alone case the 1.4.0(b)/1.5.0 notes above both name as ordinarily NOT
# earning a bump, but this one is a genuine new documented capability on an existing route's
# response contract (the SAME reasoning `include_superseded` earned 1.4.0 for): `GET
# /d/{deployment}/health` gains FOUR new `CapabilityManifest` fields (s58_missives/
# s60_entitlement/s61_signatures/s64_delegation, extending the manifest past its s45 stopping
# point) and ONE new top-level field (`identity_enforcement`, row 318's promised field --
# surfaces the deployment's effective grace/enforce posture, previously undetectable remotely,
# UPDATE survey erratum). `protocol_version`/`WIRE_PROTOCOL_VERSION` stays UNCHANGED -- every new
# field is additive; an existing client that ignores an unknown `HealthResponse` key does not
# misparse (the same rule `max_sse_clients`/`sse_poll_interval_secs` were held to one version ago).
# Bumped to 1.7.0 (work item boundary-verdict-read-surface, ledger row 221): ONE new route
# SHAPE, `GET /d/{deployment}/attestation` -- serves the latest BANKED verify-chain/judge/doctor
# result labeled as this service's own last-known attestation (serving/README.md's two-trust-
# roots section), never running any of the three instruments itself. Also gains one new
# VIEW_REGISTRY member, `work_role_census` (work item boundary-role-census-view, ledger row
# 203) -- registry-only growth, which per the 1.4.0(b) note above this version deliberately does
# NOT count on its own; named here only for this comment's own completeness. protocol_version/
# WIRE_PROTOCOL_VERSION stays UNCHANGED (a wholly new, opt-in route an existing client never
# calls does not make it misparse anything it already relies on).

# design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md's mechanism item 1: the CLOSED, spec-enumerated
# view allowlist `GET /d/{deployment}/views/{view}` serves -- the v1 membership named verbatim in
# the amendment spec. Each entry names (a) the view/table's own natural ordering KEY COLUMN,
# (b) that column's KIND -- "id" (a bigint, ledger-row-shaped column; paginated exactly like
# `/rows/current`'s own `after_id`/`limit`) or "slug" (a text natural key; paginated exactly like
# `/work/items`'s own `after_slug`/`limit` keyset, A11's discipline) -- and, as of the ledger
# rows 153/154 fix round below, (c) whether that key column is UNIQUE per row. No THIRD
# PAGINATION SHAPE is invented here -- every entry still reuses one of the two shapes this
# service already established (ADR-0012 P1); the fix round adds a per-shape TIEBREAKER, not a
# third shape.
#
# THE FIX ROUND (ledger rows 153/154, coordinator fresh-context review of commit 6a104c0,
# CRITICAL finding). `WHERE key_col > cursor ORDER BY key_col LIMIT` -- this registry's own
# pagination predicate since the v1 amendment -- SILENTLY DROPS rows whenever a NON-unique key
# value straddles a page boundary: once any one row carrying value V is served, every row NOT
# YET served that ALSO carries V is permanently unreachable (`key_col > V` excludes them all).
# Live-reproduced (limit=1 keyset walk, paginated total < direct total) on BOTH commit 6a104c0's
# new non-unique members (discharging_attest: two attests regarding one row; work_violation_
# history: two violation kinds on one slug) AND on re-audit of the pre-existing registry
# (ADR-0000 Rule 2(a)'s "presumption inverted: check the universe outward" -- the reviewer named
# work_item_violations.slug/model_defeated_rows.attest_id as sharing the identical route code
# and defect; auditing every OTHER member the same way found TWO MORE genuine instances,
# review_gap.id and work_review_gap.slug, both empirically reproduced with a constructed
# duplicate-key fixture -- see seen-red/boundary-read-surface/red.txt's fix-round section for
# the four reproductions' actual output). A SEVENTH member, missive_stale.id, is marked non-
# unique on STRUCTURAL grounds only (its own JOIN can fan out one original send across more than
# one matching reply) -- not empirically reproduced, named honestly rather than silently
# assumed either way (its own dict-entry comment below has the reasoning and the residual).
#
# THE FIX: a per-row CONTENT tiebreaker, applied ONLY to non-unique-key views, keyed on
# `(key_col, md5(the_view_row::text))` instead of `key_col` alone -- `md5(row::text)` needs no
# per-view special-casing (it works identically for any view's column set, so it does not
# re-derive each view's own hidden identity, ADR-0012 P1/P7) and is a genuine per-row VALUE (not
# a recomputed ordinal/position -- A11's "cursor is a value" honesty, extended one column). The
# served response for a NON-unique view gains one field per row, `_page_tie` (the tiebreaker
# value the client resupplies as the new `after_tie` query param to walk past a repeated key
# value without ever silently skipping a sibling row); the served response for a UNIQUE-key view
# is BYTE-IDENTICAL to pre-fix-round (ties never occur on a genuinely unique key, so the old,
# untouched code path is kept verbatim rather than routed through the new machinery at all --
# witnessed with a literal pre/post diff on work_item_current, seen-red/boundary-read-surface/
# red.txt). `after_tie` is strictly typed (empty, or exactly 32 lowercase hex chars -- an md5
# digest's own shape) and refused, typed 422, on a unique-key view (meaningless there, never
# silently ignored -- A10's own lesson, extended a third time) or on a malformed value (never
# guessed at).
#
# ROUND 2 (coordinator's second fresh-context re-review of 6a104c0+15b2f78): round 1's own text
# here called the byte-identical-row case "unreached by every reproduction on file" -- WRONG,
# live-corrected. The reviewer constructed it with an ORDINARY write sequence (the same
# reviewer attesting the same regarded row twice; nothing in the kernel refuses a repeat
# attest), witnessed `discharging_attest` emit two rows identical including `_page_tie`, and
# watched a `limit=1` walk silently drop one forever (`> cursor` excludes BOTH twins once one
# is served, since they compare equal). REACHABLE UNDER ORDINARY USE, not dormant -- the class
# is now closed for real, not merely disclosed. `_nonunique_tie_group_sql`'s own docstring has
# the full analysis (including why a third `row_number()` ordinal was evaluated and REJECTED as
# unsound under a mid-walk append, and the mid-walk-append case worked through in full); the
# short version: a byte-identical CONTENT GROUP is now served ATOMICALLY, never split across a
# page, so there is no per-row discriminator to manufacture at all -- `limit` becomes a soft
# floor for a non-unique-key view (a page may carry more rows than requested, by exactly the
# straddling group's own size), bounded by `MAX_TIE_GROUP_EXTRA_ROWS` against a pathologically
# large duplicate-content group (a typed `tie_group_too_large` refusal, never an unbounded
# response). Witnessed (seen-red/boundary-read-surface/red.txt's own round-2 section): the
# reviewer's exact double-attest reproduction (paginated_total == direct_total == 2, BOTH rows
# served, multiset-equal); a three-identical-rows case; the mid-walk-append case itself (walk
# page 1, append a byte-identical twin, walk the remainder -- no drop, the twin joins whichever
# page reaches that group's boundary); the full 54-check round-1 suite still green; a
# unique-key view still byte-identical (no ordinal/tie leakage of any kind).
#
# A cheap, NON-blocking, PRE-EXISTING observation folded in from this same review round: an
# unbound/unrecognized query parameter is silently dropped SERVICE-WIDE by this file's own
# FastAPI routing (e.g. `after_tie` supplied on `/rows/current`, a route that never declares
# it, or any unknown param on any route here) -- ordinary FastAPI/Starlette behavior, not
# specific to this fix, and not addressed here (service-wide param strictness is its own,
# separate commission; named so it is not silently unnoticed, per the SAME "surface a hazard
# you see, don't silently pass it" reflex this whole fix round is an instance of).
#
# ROUND 3 (coordinator's THIRD fresh-context re-review). ONE CRITICAL, the other half of this
# whole stack's own contract: `serving/boundary_cli_client.py`'s `get_all_rows` -- the ACTUAL,
# PRODUCTION walker `bootstrap/templates/led.tmpl`/`pickup.tmpl` use, as opposed to this
# fixture family's own test-only walker -- was never taught the `after_tie` contract rounds 1-2
# minted server-side. Since `after_tie` defaults to `""` server-side and any real md5 digest
# sorts strictly greater than `""`, every "next page" request this production client issued
# kept re-supplying the SAME already-served key group forever -- live-witnessed by the reviewer
# as a genuine infinite loop against `review_gap` (a view `led.tmpl` genuinely walks) at
# `limit=1`. Fixed in `get_all_rows` itself (see its own docstring); rounds 1-2's SQL design was
# correct and UNREACHED by its one real consumer until this round. Two client-visible contract
# changes land alongside it, both DISCLOSED here rather than left implicit: (a)
# `tie_group_too_large` (`_tie_group_too_large`, above) now answers HTTP 409, not 500 -- this
# file's own convention reserves 500 for `unclassified_failure` alone, and this refusal is a
# boundary-understood business rule, not an unclassifiable psql failure; (b) `GET /meta` gains
# a fourth fact, `max_tie_group_extra_rows` (`MetaResponse`'s own amendment note,
# boundary_models.py), the `MAX_TIE_GROUP_EXTRA_ROWS` bound made visible so a caller can plan
# around a `tie_group_too_large` refusal rather than discover the bound only by hitting it
# (ADR-0016: an advertised limit is part of the contract).
#
# A SIBLING HAZARD in the SAME table, fixed in the SAME pass (boundary_cli_client.py's own
# `_ID_FIELD_OVERRIDE`/`_SLUG_FIELD_OVERRIDE`, its own disclosed duplication of this registry's
# key-column choices): `discharging_attest` and `work_bookkeeping_closes` (this build's own new
# views) had no override entry for their non-'id' key columns, so a `get_all_rows(cursor=
# "after_id")` caller would KeyError on page 1 -- the reviewer's own named instances. Auditing
# EVERY registry member the same way (this stack's own by-now-standing discipline) found the
# identical, PRE-EXISTING gap on `work_edge_blocks_close` (this build's own third new view) and
# on FOUR views predating this build entirely -- `principal_relations`/`principal_role_
# bindings`/`principal_keys`/`principal_competences` (kernel/lineage/s41's own D-5 views,
# registered in this dict since the legacy-led-retirement inventory pass, ledger row 1149) --
# none of which ever had an override entry despite all four keying on `row_id`, not `id`. Fixed
# in the same commit; see `boundary_cli_client.py`'s own `_ID_FIELD_OVERRIDE` comment for the
# full accounting.
#
# Key-column choice, per entry, named once here rather than re-derived per request:
#   question_status.question_id           -- kernel/lineage/s31 (q.id, a ledger row id, aliased).
#                                             UNIQUE (plain WHERE over ledger_current, q.id is the
#                                             view's own FROM-clause primary key, no join fan-out).
#   review_gap.id                         -- kernel/lineage/s15+ (l.id, a ledger row id). NOT
#                                             UNIQUE -- fix-round finding: `JOIN countersign_
#                                             obligation o ON o.obliges_actor = l.actor` fans out
#                                             one undischarged row `l` across EVERY obligation
#                                             scope currently obliging that row's own actor; an
#                                             actor obliged under two scopes at once (ordinary,
#                                             not a misconfiguration) produces two review_gap rows
#                                             sharing the SAME id. Empirically reproduced (fix
#                                             round's own uniqueness probe: id=29 served twice).
#   review_stamp_distinctness.review_id   -- kernel/lineage/s17+ (r.id, a ledger row id, aliased).
#                                             UNIQUE (JOIN g ON g.id = r.regards is an equality
#                                             join to exactly one ledger row, g.id being a PK).
#   standing_decisions.id                 -- kernel/lineage/s36 (a ledger row id). UNIQUE (plain
#                                             WHERE over ledger_current, no join).
#   countersign_obligation.scope          -- kernel/lineage/s15 (a TABLE, PRIMARY KEY scope, text).
#                                             UNIQUE (a literal database primary key).
#   work_item_violations.slug              -- kernel/lineage/s22+ (work_slug, text). NOT
#                                             target_id (added only at s37) -- live-witnessed
#                                             against this repo's own pre-s37 `autoharn1` world
#                                             (lineage head s30): a target_id-keyed route 500'd
#                                             (`column "target_id" does not exist`) on a view
#                                             that legacy `led work violations`'s own `SELECT
#                                             slug FROM work_item_violations` reads fine, because
#                                             that query never needed target_id at all. slug is
#                                             the column present on every lineage shape this view
#                                             has ever had. NOT UNIQUE per row -- a slug can carry
#                                             more than one violation class; the fix-round's
#                                             composite tiebreaker is what actually closes the
#                                             pagination-loss gap this was previously (wrongly)
#                                             described as merely "living with."
#   work_review_gap.slug                  -- kernel/lineage/s29+ (work_slug, text). NOT UNIQUE --
#                                             fix-round finding, empirically reproduced (a single
#                                             slug carrying two distinct deferred violation-
#                                             disposition targets serves both correctly with the
#                                             tiebreaker; without it, one silently vanished).
#   model_attestations.row_id             -- kernel/lineage/s44 (lc.id, a ledger row id, aliased).
#                                             UNIQUE (plain WHERE over ledger_current, no join).
#   model_defeated_rows.attest_id         -- kernel/lineage/s46+/s50 (a.id, a ledger row id,
#                                             aliased). NOT UNIQUE -- one attestation can match
#                                             more than one competence grant; SAME fix as above,
#                                             witnessed on a constructed-duplicate fixture leg
#                                             (fix round; the pre-fix-round comment here called
#                                             this "living with" the gap, which the reviewer
#                                             correctly read as contradicted by the CRITICAL
#                                             finding -- the tiebreaker is the actual closure).
#   credited_current.id                   -- kernel/lineage/s46 (a ledger row id, byte-identical
#                                             column shape to ledger_current). UNIQUE.
#   work_item_current.slug                -- kernel/lineage/s22+ (work_slug, text -- the SAME view
#                                             GET /work/items already serves; listed here too
#                                             because the amendment spec's own v1 allowlist names
#                                             it explicitly, a second reachable path to identical
#                                             data, not a new one)
# The two entries below are a LATER, additive registry growth under a SEPARATE spec (design/
# FABLE-RESERVATION-RESIDUE-SPEC.md section 3, maintainer-ratified 2026-07-22, kernel/lineage/
# s56-reservation-residue.sql) -- no new ROUTE, no new pagination shape, the same closed-registry
# mechanism the v1 amendment above established, extended the same way model_attestations/
# model_defeated_rows/credited_current already were (later kernel deltas, same registry, no
# BOUNDARY_SERVICE_VERSION bump -- the version names the ROUTE-TABLE closure, unaffected by a
# registry-membership growth):
#   reservations_outstanding.review_id    -- kernel/lineage/s56 (r.id, a ledger row id, aliased)
#   review_verdicts.review_id             -- kernel/lineage/s56 (r.id, a ledger row id, aliased)
# The two entries below are a THIRD, additive registry growth (legacy-led-retirement phase 1B,
# ledger row 1149) -- serving `led work review-gap`/`startable`/`resolve-violation`/
# `supersede-cascade`'s own reads through the boundary path, same closed-registry mechanism, no
# new route, no BOUNDARY_SERVICE_VERSION bump:
#   work_review_gap.slug                  -- already registered above (s29+); named again here
#                                             only in this comment's own cross-reference, not a
#                                             second dict entry (see the pre-existing line below)
#   work_edge_parent.child_slug           -- kernel/lineage/s32-edge-views-single-home.sql (RAW,
#                                             includes every parent-edge ever written, retracted
#                                             or not -- see that view's own COMMENT ON VIEW).
#                                             child_slug is the natural key: validate_work_item()
#                                             (s22+) refuses a duplicate opening act per slug, so
#                                             a slug can be the CHILD end of at most one edge ever
#                                             -- unlike parent_slug, which repeats once per child.
#   work_startable.slug                   -- kernel/lineage/s39-blocks-start.sql (work_slug, text
#                                             -- the SAME natural key work_item_current already
#                                             uses one view over)
# A FOURTH additive registry growth (legacy-led-retirement inventory pass, ledger row 1149,
# closing the coverage-diff's own witnessed gap -- `led principal grant-competence`/`relate`
# and their six siblings were the only remaining NOT-COVERED family): the four s41 D-5 derived
# binding views (kernel/lineage/s41-principal-bindings-and-relations.sql), each already carrying
# a `row_id` column (the carrying event's own ledger id -- an id-shaped natural key, same
# pagination shape as review_stamp_distinctness/reservations_outstanding above). No new route,
# no BOUNDARY_SERVICE_VERSION bump -- same mechanism, fourth use.
#   principal_relations.row_id       -- s41 D-5 (relate/unrelate)
#   principal_role_bindings.row_id   -- s41 D-5 (bind-role/release-role)
#   principal_keys.row_id            -- s41 D-5 (bind-key/revoke-key)
#   principal_competences.row_id     -- s41 D-5 (grant-competence/withdraw-competence)
# A SIXTH additive registry growth (ledger rows 153/154, work item view-registry-decomposition-
# views; experience4 panel requests, missive receipt row 149 verbatim: the panel names SEVEN
# views for an obligation-tree derivation and a commission-decomposition rendering). Two of the
# seven are DELIBERATELY EXCLUDED here, not silently -- both genuinely exist in the s15..s68
# lineage (verified by reading their CREATE VIEW below), but NEITHER carries any column this
# registry's two established pagination shapes (an "id"-shaped bigint or a "slug"-shaped text
# NATURAL KEY, per this dict's own leading comment) can safely key on, and inventing a third
# shape is exactly what the amendment spec and this registry's own closed-enumeration posture
# forbid:
#   work_edge_obligation   -- EXCLUDED. kernel/lineage/s32-edge-views-single-home.sql's own
#                             SELECT projects only (from_slug, to_slug) -- the ledger row id each
#                             arm joins against (`lc.id`) is consulted for the in-force filter
#                             but never SELECTed, so no row-identifying column survives the
#                             UNION ALL at all. Worse than the "disclosed non-unique slug"
#                             precedent above (work_item_violations.slug, model_defeated_rows.
#                             attest_id): from_slug is a graph ADJACENCY column, so a real work
#                             tree can hang many out-edges off one from_slug -- keyset-paginating
#                             on it (`WHERE from_slug > cursor`) would silently drop every
#                             remaining edge sharing a from_slug the moment any ONE of them is
#                             served past the cursor, on every page boundary that happens to
#                             land inside a repeated value, not merely at a rare tie (ADR-0002:
#                             a silent, class-shaped data loss the existing "disclosed non-
#                             unique" precedent does not carry, so it is not authorized by that
#                             precedent). No column here is a value a client can safely resume
#                             from without a machine-checkable gap.
#   work_item_descendants  -- EXCLUDED. kernel/lineage/s28-work-parent-edge.sql's own SELECT
#                             projects (ancestor_slug, descendant_slug, depth) -- a recursive
#                             transitive closure, so NEITHER slug column is unique (one
#                             descendant has one row per ancestor above it in the tree, and vice
#                             versa) and neither is a graph-adjacency column in the SAME
#                             non-keyset-safe shape as work_edge_obligation's from_slug above.
#                             Same disposition, same reason: no column here is a safe keyset
#                             cursor.
# Both are real, queryable relations today -- this exclusion is a registry-membership gap, not a
# claim the views are broken or unused; `work_item_strict_blockers()` (the SQL function, kernel-
# side) already walks `work_edge_obligation` for the obligation-tree computation this commission
# was asked to serve, and a future spec MAY mint the two-arg keyset shape (`ORDER BY from_slug,
# <ledger-id tiebreaker> WHERE (from_slug, id) > (cursor_slug, cursor_id)`) these views would
# need -- that is new pagination-shape design, a Fable-authored spec's job (CLAUDE.md
# ORCHESTRATION), not a registry entry authored in passing here. The remaining FIVE views serve
# safely under the two existing shapes, verified per-view below (CREATE VIEW cited, key column
# uniqueness checked against the SAME "disclosed non-unique is fine, no-column-at-all is not"
# discriminator):
#   work_edge_blocks_close.edge_row_id     -- kernel/lineage/s32-edge-views-single-home.sql. The
#                                             work_depends_on row's own ledger id, SELECTed
#                                             directly (unlike work_edge_obligation one view
#                                             over) -- id-shaped, unique per row (one
#                                             blocks-close edge is one work_depends_on row).
#   discharging_attest.regards_id          -- kernel/lineage/s32-edge-views-single-home.sql,
#                                             widened in place by kernel/lineage/
#                                             s56-reservation-residue.sql (verdict IN ('attest',
#                                             'attest_with_reservations'), column list
#                                             UNCHANGED). regards_id is id-shaped but NOT UNIQUE
#                                             (more than one actor can attest the same row) --
#                                             CRITICAL FINDING, fix round (ledger rows 153/154,
#                                             coordinator fresh-context review): live-reproduced
#                                             silently dropping the second attest at a limit=1
#                                             page boundary before the composite-tiebreaker fix
#                                             above; the pre-fix-round text here called this
#                                             "safe because it matches a precedent" -- WRONG, the
#                                             precedent (model_defeated_rows.attest_id) carried
#                                             the identical live bug, not a tolerated residual.
#                                             Fixed by the (key_col, md5(row::text)) composite
#                                             keyset (see this dict's own leading comment); GREEN
#                                             witnessed on the reviewer's own reproduction (two
#                                             attests regarding one row, limit=1, paginated total
#                                             == direct total), red.txt.
#   work_violation_history.slug            -- kernel/lineage/s37-violation-disposition.sql,
#                                             re-issued by kernel/lineage/s39-blocks-start.sql
#                                             (adds the blocks_start_cycle arm, unchanged column
#                                             list: violation, slug, detail, target_id,
#                                             disposition_id, disposition_resolution,
#                                             disposition_basis, disposition_witness,
#                                             disposition_in_force, target_in_force,
#                                             target_retraction_id). slug is text, NOT UNIQUE (a
#                                             slug can carry more than one violation class) --
#                                             CRITICAL FINDING, fix round, SAME as
#                                             discharging_attest immediately above (this view's
#                                             own precedent citation, work_item_violations.slug,
#                                             carried the identical live bug too -- both now fixed
#                                             by the same composite-tiebreaker mechanism, not
#                                             merely both "sharing a residual").
#   work_bookkeeping_closes.close_id       -- kernel/lineage/s38-bookkeeping-close.sql. close_id
#                                             is the work_closed row's own ledger id, SELECTed
#                                             directly -- id-shaped, unique per row (one
#                                             bookkeeping close is one work_closed row).
#   countersigned_in_force.id              -- present since kernel/lineage/
#                                             s20-obligation-grants-and-view-refresh.sql, latest
#                                             re-issue kernel/lineage/
#                                             s68-typed-absence-dispositions.sql (the +2-column
#                                             s68 append -- refusal_attempted_kind_disposition,
#                                             refusal_attempted_actor_disposition -- ledger row
#                                             153's own build touching this same lineage delta).
#                                             SAME full ledger-row column shape as ledger_current
#                                             (id, ts, session, kind, ... every ledger column)
#                                             further filtered to rows an in-force discharging_
#                                             attest regards -- id is the ledger row's own bigint
#                                             id, unique per row, the identical shape /rows/
#                                             current already serves (this view exposes NO column
#                                             /rows/current does not already serve; the
#                                             boundary's read posture is unchanged by adding it).
#                                             MODERATE DISCLOSURE (fix round, ledger rows
#                                             153/154, coordinator fresh-context review): the
#                                             MAIN boundary-read-surface fixture's own world stops
#                                             at s59 (a separate, DOCUMENTED, s61-possession-ref
#                                             blocker -- see that fixture's own CHAIN_FULL
#                                             comment), so its WR1 GREEN validates this view's
#                                             pre-s68 (s67-headed, two columns short) shape, NOT
#                                             the true, current s68 shape the row-153 build
#                                             actually shipped. A SEPARATE, minimal, s68-headed
#                                             scratch world (WR7 in that same fixture file) that
#                                             skips the ONE act (principal_key_bound) the s61
#                                             blocker requires exercises the true s68 shape
#                                             instead -- confirming both new columns are present
#                                             and the row set still matches a direct read at s68.
VIEW_REGISTRY: dict[str, tuple[str, str, bool]] = {
    "question_status": ("question_id", "id", True),
    "review_gap": ("id", "id", False),
    "review_stamp_distinctness": ("review_id", "id", True),
    "standing_decisions": ("id", "id", True),
    "countersign_obligation": ("scope", "slug", True),
    "work_item_violations": ("slug", "slug", False),
    "work_review_gap": ("slug", "slug", False),
    "model_attestations": ("row_id", "id", True),
    "model_defeated_rows": ("attest_id", "id", False),
    "credited_current": ("id", "id", True),
    "work_item_current": ("slug", "slug", True),
    # design/FABLE-RESERVATION-RESIDUE-SPEC.md section 3 (kernel/lineage/s56-reservation-
    # residue.sql): both new views key on review_id (bigint) -- id-shaped pagination, the same
    # shape review_stamp_distinctness already uses one row over.
    "reservations_outstanding": ("review_id", "id", True),
    "review_verdicts": ("review_id", "id", True),
    # legacy-led-retirement phase 1B (ledger row 1149) -- see this dict's own leading comment.
    "work_edge_parent": ("child_slug", "slug", True),
    "work_startable": ("slug", "slug", True),
    # legacy-led-retirement inventory pass (ledger row 1149) -- see this dict's own leading
    # comment, fourth registry growth.
    "principal_relations": ("row_id", "id", True),
    "principal_role_bindings": ("row_id", "id", True),
    "principal_keys": ("row_id", "id", True),
    "principal_competences": ("row_id", "id", True),
    # design/FABLE-MISSIVES-KERNEL-SPEC.md §3 (kernel/lineage/s59-missive-views.sql, ledger row
    # 1263) -- a FIFTH additive registry growth, same closed-registry mechanism, no new route, no
    # BOUNDARY_SERVICE_VERSION bump. Five of the six views key on id (bigint, id-shaped
    # pagination, the same shape reservations_outstanding/review_verdicts already use);
    # missive_open_threads keys on missive_thread (slug-shaped, the work_startable/
    # work_edge_parent precedent).
    "missive_outbound": ("id", "id", True),
    "missive_receipts": ("id", "id", True),
    "missive_undisposed": ("id", "id", True),
    # missive_stale.id: CONSERVATIVELY marked non-unique (fix round, ledger rows 153/154) -- its
    # own JOIN matches a `missive_undisposed` row against EVERY `missive_received` row citing it
    # as `missive_responds_to` (a reply-count, not an equality-to-one-row join); nothing in the
    # kernel schema forecloses two replies citing the same original, so `id` (the ORIGINAL
    # send's id, repeated once per matching reply) can repeat. Not empirically reproduced (this
    # fix round's own uniqueness probe could not clear the s58 missive-world-identity birth
    # ceremony in the time available -- see the fix-round report), so this is a STRUCTURAL
    # classification, not a witnessed one; named honestly rather than silently assumed safe.
    "missive_stale": ("id", "id", False),
    "missive_delivery_audit": ("id", "id", True),
    "missive_open_threads": ("missive_thread", "slug", True),
    # A SIXTH additive registry growth (ledger rows 153/154) -- see this dict's own leading
    # comment for the full per-view key-column derivation and the two named exclusions
    # (work_edge_obligation, work_item_descendants).
    "work_edge_blocks_close": ("edge_row_id", "id", True),
    "discharging_attest": ("regards_id", "id", False),
    "work_violation_history": ("slug", "slug", False),
    "work_bookkeeping_closes": ("close_id", "id", True),
    "countersigned_in_force": ("id", "id", True),
    # A SEVENTH additive registry growth (work item boundary-role-census-view, ledger row 203):
    # the APPROVED role-census read -- see `_role_census_sql`'s own docstring immediately below
    # for the full shape. slug-keyed, UNIQUE (one row per work item, the SAME natural key
    # work_item_current already uses one entry above) -- deliberately NOT a new pagination shape.
    "work_role_census": ("slug", "slug", True),
}

# NO KERNEL CHANGE (row 203's own instruction, honored): `work_role_census` names no stored
# relation kernel/lineage ever creates -- the served role (`GRANT USAGE ON SCHEMA` only,
# kernel/lineage/s15-schema.sql) holds no `CREATE` privilege on `:"schema"` to mint one at
# runtime either (verified by reading that GRANT list, not assumed), so a genuine `CREATE VIEW`
# object is not an option here without a privilege change this row's own scope does not license.
# This is therefore a SERVING-SIDE view in the literal sense: its SELECT text lives here, in
# Python, authored by this layer rather than a kernel/lineage delta -- composed ENTIRELY from
# relations the served role already holds SELECT on (`ledger`, `review_detail`, both granted at
# s15), the same raw-table-read posture `rows_asof`/`rows_current?include_superseded=true`
# already use one route over. `_view_from_clause` below is the ONE seam that lets
# `views_view`'s shared pagination/capability-gate code treat this exactly like a stored view
# (wrapped as a derived table, `(<select>) AS work_role_census`) without touching a single byte
# of the twenty-two PRE-EXISTING VIEW_REGISTRY members' own code path (every one of them still
# resolves `FROM {cfg.schema}.{view}` literally, unchanged).
_ROLE_CENSUS_DERIVED_VIEWS: frozenset[str] = frozenset({"work_role_census"})


def _role_census_sql(schema: str) -> str:
    """The role-census SELECT (work item boundary-role-census-view, row 203; doctrine:
    user-guide/recipes/IDENTITY-AND-AUTHORITY.md's "Work-unit role assignment" section). One row
    per work item (`opened` is the driving CTE, LEFT JOINed against the rest -- an item with no
    claim/close/review yet still gets a row, matching `work_item_current`'s own LEFT JOIN shape
    one view over): opener (the `work_opened` row's own actor), EVERY claim in claim order as a
    `claimants` JSON array (each entry flagged `is_reclaim_by_distinct_actor` -- the doctrine's
    own words: "that claim-over-a-live-claim by a distinct actor IS the handoff's entire record"),
    the claimant-of-record (the LATEST claim, the same `DISTINCT ON ... ORDER BY id DESC`
    resolution `work_item_current` already uses), the closer (if closed), and every REVIEWER
    whose review `regards` a row carrying this item's `work_slug` (covers close-attestation
    review AND the decomposition-review doctrine item -- both `work_closed` and `work_opened`
    rows carry `work_slug`), each with its KERNEL-COMPUTED `discharge_grade`
    (`review_detail.discharge_grade`, s34: "computed by the kernel ... never writer-asserted" --
    this view reads it, never derives a second, boundary-invented grade of its own, ADR-0012 P2).

    Named consumers (row 203's own instruction, stated once here rather than only in the ledger
    claim): `./pickup`-time hydration ("who owns what right now") and post-hoc RCA ("who was
    accountable when this shipped") -- IDENTITY-AND-AUTHORITY.md's own words, verbatim, for why
    this view exists at all (the named-consumer test).

    SCOPE, HONESTLY NAMED: a reviewer's `regards` is resolved ONE HOP (the review's own row,
    never walked through a chain of supersessions to some earlier antecedent) -- the same
    resolution depth `review_stamp_distinctness`/`work_review_gap` already commit to one view
    over; a review that regards a SUPERSEDED close/open row for this slug still surfaces here
    (append-only history, not filtered to only the in-force row), which is the correct behavior
    for a POST-HOC RCA consumer (row 203's own second named use) even though a "who currently
    owns this" reading would want the in-force-only subset -- `pickup` hydration's own caller
    filters for currency the same way it already does for `work_item_current`'s `state` column."""
    return (
        "WITH opened AS ("
        "  SELECT id AS opened_id, work_slug AS slug, actor AS opener, ts AS opened_ts"
        f" FROM {schema}.ledger WHERE kind = 'work_opened'"
        "), claims_ordered AS ("
        "  SELECT id AS claimed_id, work_slug AS slug, actor AS claimant, ts AS claimed_ts,"
        "         lag(actor) OVER (PARTITION BY work_slug ORDER BY id) AS prev_claimant"
        f" FROM {schema}.ledger WHERE kind = 'work_claimed'"
        "), claims AS ("
        "  SELECT slug,"
        "         jsonb_agg(jsonb_build_object("
        "           'claimed_id', claimed_id, 'claimant', claimant, 'claimed_ts', claimed_ts,"
        "           'is_reclaim_by_distinct_actor',"
        "           (prev_claimant IS NOT NULL AND prev_claimant IS DISTINCT FROM claimant)"
        "         ) ORDER BY claimed_id) AS claimants,"
        "         bool_or(prev_claimant IS NOT NULL AND prev_claimant IS DISTINCT FROM claimant)"
        "           AS any_reclaim_by_distinct_actor"
        "  FROM claims_ordered GROUP BY slug"
        "), claimant_of_record AS ("
        "  SELECT DISTINCT ON (work_slug) work_slug AS slug, actor AS claimant_of_record,"
        "         id AS claimant_of_record_claimed_id"
        f" FROM {schema}.ledger WHERE kind = 'work_claimed'"
        "  ORDER BY work_slug, id DESC"
        "), closed AS ("
        "  SELECT DISTINCT ON (work_slug) work_slug AS slug, id AS closed_id, actor AS closer,"
        "         ts AS closed_ts"
        f" FROM {schema}.ledger WHERE kind = 'work_closed'"
        "  ORDER BY work_slug, id DESC"
        "), reviewers AS ("
        "  SELECT wl.work_slug AS slug,"
        "         jsonb_agg(jsonb_build_object("
        "           'review_id', r.id, 'reviewer', r.actor, 'regards', r.regards,"
        "           'verdict', d.verdict, 'independence', d.independence,"
        "           'discharge_grade', d.discharge_grade, 'ts', r.ts"
        "         ) ORDER BY r.id) AS reviewers"
        f" FROM {schema}.ledger r"
        f" JOIN {schema}.review_detail d ON d.ledger_id = r.id"
        f" JOIN {schema}.ledger wl ON wl.id = r.regards AND wl.work_slug IS NOT NULL"
        "  WHERE r.kind = 'review'"
        "  GROUP BY wl.work_slug"
        ") "
        "SELECT o.slug, o.opener, o.opened_id, o.opened_ts,"
        "       coalesce(c.claimants, '[]'::jsonb) AS claimants,"
        "       cor.claimant_of_record, cor.claimant_of_record_claimed_id,"
        "       cl.closer, cl.closed_id, cl.closed_ts,"
        "       coalesce(c.any_reclaim_by_distinct_actor, false) AS any_reclaim_by_distinct_actor,"
        "       coalesce(rv.reviewers, '[]'::jsonb) AS reviewers "
        "FROM opened o "
        "LEFT JOIN claims c ON c.slug = o.slug "
        "LEFT JOIN claimant_of_record cor ON cor.slug = o.slug "
        "LEFT JOIN closed cl ON cl.slug = o.slug "
        "LEFT JOIN reviewers rv ON rv.slug = o.slug"
    )


def _view_from_clause(cfg: BoundaryConfig, view: str) -> str:
    """The ONE seam `views_view` resolves its FROM target through -- returns the literal,
    byte-identical `{schema}.{view}` for every PRE-EXISTING VIEW_REGISTRY member (unchanged code
    path), or a parenthesized derived table aliased as `{view}` for a `_ROLE_CENSUS_DERIVED_VIEWS`
    member (currently the one, `work_role_census`) -- so the SAME shared pagination/tiebreaker
    code below never needs to know which kind of relation it is querying."""
    if view in _ROLE_CENSUS_DERIVED_VIEWS:
        return f"({_role_census_sql(cfg.schema)}) AS {view}"
    return f"{cfg.schema}.{view}"

# The s43 boundary functions, named ONCE (ADR-0012 P1) -- the write-route table (spec §4) is
# built from this dict, never re-typed per route. `obligation_revoke` (design/FABLE-LEGACY-LED-
# RETIREMENT-SPEC.md Part A, kernel/lineage/s57-obligation-revocation-event.sql) is the sixth
# such function and its own tiny (scope/reason/actor) payload fits the generic psql `-v` transport
# comfortably -- unlike artifact_write (Part B, below), which needs its own dedicated route
# because its payload can approach ~1.4 MiB (see `artifact_put`'s own docstring).
WRITE_SURFACES: dict[str, str] = {
    "ledger": "ledger_write",
    "review": "review_write",
    "registration": "registration_write",
    "obligation": "obligation_write",
    "obligation_revoke": "obligation_revoke",
    # design/FABLE-MISSIVES-KERNEL-SPEC.md §2.7 (kernel/lineage/s58-missive-substrate.sql, ledger
    # row 1263): the SEVENTH SECURITY DEFINER boundary function, the two-row disposition+
    # acknowledgment ceremony. Its (receipt/disposition/statement/actor) payload fits the generic
    # psql `-v` transport comfortably (the obligation_revoke precedent) -- no dedicated route.
    # missive_sent/missive_received/belief ride the generic `ledger` surface above unchanged
    # (missive_* payload keys pass ledger_write's generic key validation with zero edits, s53's
    # own precedent for kind-scoped columns).
    "missive_dispose": "missive_dispose",
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
    "obligation_revoke": ObligationRevokeWriteIntFields,
    "missive_dispose": MissiveDisposeWriteIntFields,
    # "artifact" is deliberately NOT keyed through WRITE_SURFACES/make_write_route (Part B's own
    # dedicated route, artifact_put, reuses this SAME dict directly via
    # `_bound_write_payload_ints("artifact", payload)` -- see that route's own docstring for why).
    "artifact": ArtifactWriteIntFields,
}

# A deployment.json identifier (schema/kern/role) must look like a plain SQL identifier --
# refused at construction time otherwise (ADR-0002 rung 1); this is the one guard that lets
# every query below interpolate schema/kern/role as bare text safely.
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}

# design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part B: the artifact store's own content-addressed
# key shape (kernel/lineage/s51-artifact-store.sql's `artifact_hash_shape` CHECK, mirrored here
# for a path-parameter-level typed 422, the SAME idiom `_out_of_range_id` already establishes for
# id-typed parameters -- never let a malformed hash reach psql's own text-literal interpolation).
_ARTIFACT_HASH_RE = re.compile(r"^[0-9a-f]{64}$")

# A2.2/A8's raw-body write-ingress bounds (checkpoint a: raw body, BEFORE any JSON parsing,
# enforced at `_read_bounded_body`; checkpoint b: the re-serialized psql `-v` argument, enforced
# in `make_write_route`'s handler, typed 413 naming this wall). ADR-0012 P1: one home, not one
# literal per checkpoint -- both bounds, their full rationale, and MAX_WRITE_BODY_BYTES's kernel
# twin now live in serving/bounds.py (see this module's docstring, "SIZE AXIS").

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

# Round-2 fix (ledger rows 153/154, coordinator's second fresh-context re-review of 6a104c0+
# 15b2f78): a byte-identical-content tie group (see `views_view`'s non-unique-key branch and
# VIEW_REGISTRY's own leading comment for the full reasoning) is served ATOMICALLY -- never
# split across a page -- which means a page can legitimately carry more rows than `limit` asked
# for, by however many extra members the tie group at the page boundary happens to have. This
# is the ONE named exception to the transport-level `1 <= limit <= 1000` bound every other route
# in this file enforces. MAX_TIE_GROUP_EXTRA_ROWS bounds how far that exception is allowed to
# stretch: if the group truly has more members than this, the boundary refuses the page loudly
# (ADR-0002) rather than serve an unboundedly large response -- a pathologically large content-
# identical group (an actor writing the same duplicate act thousands of times) is a real,
# if unlikely, denial-of-service shape a keyset route must not absorb silently.
MAX_TIE_GROUP_EXTRA_ROWS = 1000

# A9: the concurrency admission bound (ADR-0012 P1: one named constant, not a per-handler
# literal). Deliberately UNDER the ASGI threadpool's own default concurrency (anyio's 40 tokens
# on the review host) so kernel-call occupancy alone can never starve non-kernel work or
# /health's own thread dispatch -- the threadpool size stops being load-bearing; this service's
# own named constant is the bound. `_KERNEL_CALL_SEMAPHORE` is the ONE shared gate every kernel
# call passes through (see `_psql`'s own docstring, "ADMISSION AXIS"); `threading.BoundedSemaphore`
# is thread-safe and matches the plain-`def`/threadpool handler shape A3.1 already established
# (a real OS thread per in-flight handler, not a coroutine).
#
# MULTIPLEX SPEC §4: this constant stays the GLOBAL bound -- it protects the shared threadpool,
# which is process-wide, not per-deployment -- and is UNCHANGED by multiplexing. The
# per-deployment sub-bound (`MAX_INFLIGHT_PER_DEPLOYMENT`) is a SECOND, independent gate, sized
# per process at startup by `compute_per_deployment_limit` below and held one-per-deployment on
# each `BoundaryConfig` (never a second literal here -- ADR-0012 P1).
MAX_INFLIGHT_KERNEL_CALLS = 24
_KERNEL_CALL_SEMAPHORE = threading.BoundedSemaphore(MAX_INFLIGHT_KERNEL_CALLS)


def compute_per_deployment_limit(n_deployments: int) -> int:
    """Multiplex spec §4: `MAX_INFLIGHT_PER_DEPLOYMENT = max(4, MAX_INFLIGHT_KERNEL_CALLS //
    len(deployments))`, computed once at startup (never re-derived per request) and PRINTED at
    startup (spec §4, verbatim) so an operator can see the bound their own deployment count
    produced. The floor of 4 keeps a many-deployment config from squeezing any single
    deployment's own sub-bound down to a value so small ordinary concurrent use of THAT
    deployment alone would trip it."""
    return max(4, MAX_INFLIGHT_KERNEL_CALLS // n_deployments)

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

# A11 item 1: `/work/items`' cursor domain bound. ADR-0012 P1: named ONCE, not an inline literal
# at the one call site that checks it -- now in serving/bounds.py (see its own docstring for the
# full rationale).



# ================================================================================================
# IDENTITY CONDUIT (design/FABLE-DISPATCH-MECHANICS-SPEC.md, ledger rows 1463/1467/1468/1471) --
# the one HTTP-borne identity plumbing serving both a human operator's vendor stamp and a
# dispatched sub-agent's minted principal. §1's trust property, verbatim: this service is a
# CONDUIT, never an authority -- it never holds key material, never computes or verifies an
# HMAC, never rewrites a value it did not itself construct from a bounded, validated header.
#
# HEADER NAMES (this build's own choice, in the service's existing kebab-case idiom -- FastAPI/
# Starlette lower-cases and hyphen-normalizes header names on read, so these are matched
# case-insensitively regardless of how a client capitalizes them). The vendor-stamp headers name
# is deliberately `X-Autoharn-Vendor-*`, mirroring the app.vendor_* GUC names verbatim
# (kernel/lineage/s17-stamp-mechanism.sql, s23-per-invocation-stamp-token.sql) so the header <->
# GUC correspondence is legible without a lookup table:
IDENTITY_HEADER_VENDOR_SESSION = "x-autoharn-vendor-session"
IDENTITY_HEADER_VENDOR_AGENT = "x-autoharn-vendor-agent"
IDENTITY_HEADER_VENDOR_TS = "x-autoharn-vendor-ts"
IDENTITY_HEADER_VENDOR_HMAC = "x-autoharn-vendor-hmac"
IDENTITY_HEADER_VENDOR_INVOCATION = "x-autoharn-vendor-invocation"  # optional; s23, capture-only
# The minted-principal channel. FINDING, STATED HONESTLY (this build's own reading of the
# kernel lineage, per the commission's "derive the exact GUC names ... never invent"): no
# current_setting()-consulting GUC for a MINTED principal's identity exists anywhere in
# kernel/lineage/*.sql (grepped: s40/s41/s64 attribute a write's `actor` column either from the
# CONNECTING DB ROLE via `principal_role`/`set_actor` -- kernel/lineage/
# s40-principal-identity-events.sql Element 6 -- or from an explicit `actor` value the CALLER
# supplies on the write payload; s64's own delegation-condition columns are consulted via the
# `principal_relations` view/chain walk, keyed on that SAME `actor` column, never a GUC). The
# vendor stamp's app.vendor_* GUCs (above) are the ONLY per-request GUC channel this kernel
# lineage actually reads. The minted-principal identity therefore threads through the EXISTING,
# already-accepted `actor` JSON field on write payloads (serving/README.md, "The write path --
# attribution, honestly limited": "the service passes a write payload's actor key through
# unchanged if the caller supplied one") -- this header lets the SERVICE itself set that field
# from a validated identity fact, rather than trusting whatever the caller's own JSON body
# claims, when a dispatched agent's own dispatch-mint stamp is present.
IDENTITY_HEADER_MINTED_PRINCIPAL = "x-autoharn-minted-principal"

# Every identity header value is bounded (refused with IdentityHeaderInvalid BEFORE any kernel
# call -- never truncated, never passed through, spec §1 verbatim); the bound itself, its s65
# house-precedent rationale, and its kernel-side twin now live in serving/bounds.py.

# A vendor HMAC is a sha256 hex digest (kernel/lineage/s17-stamp-mechanism.sql's own
# `stamp_valid`: `encode(hmac(..., 'sha256'), 'hex')`) -- exactly 64 lowercase hex characters.
# This service never COMPUTES or VERIFIES the HMAC (the conduit invariant); this regex only
# refuses a value that could not possibly BE one, before it ever reaches the kernel's own
# verification (a malformed value would fail set_stamp's own hmac comparison anyway, landing
# stamp_verified=false -- refusing it here is an earlier, more specific, typed teaching refusal,
# not a second authority).
_VENDOR_HMAC_RE = re.compile(r"^[0-9a-f]{64}$")


class _IdentityRefusal(Exception):
    """Raised by `_parse_identity_headers` for an oversized or malformed identity header --
    caught in the ONE place (the diagnostic-logging middleware, which now also owns identity
    parsing) that turns it into the typed `IdentityHeaderInvalid` response, BEFORE `call_next`
    ever runs (so no route handler, and no `_psql` call, is ever reached)."""

    def __init__(self, header: str, message: str) -> None:
        super().__init__(message)
        self.header = header
        self.message = message


def _bounded_header(headers, name: str) -> str | None:
    """Reads one header, refusing (never truncating) a value over `IDENTITY_HEADER_MAX_BYTES`.
    Returns None when the header is simply absent (the ordinary, unstamped case) -- absence is
    never itself a refusal; only PRESENT-but-oversized is."""
    v = headers.get(name)
    if v is None:
        return None
    if len(v.encode("utf-8", "surrogatepass")) > IDENTITY_HEADER_MAX_BYTES:
        raise _IdentityRefusal(
            name, f"identity header {name!r} is {len(v.encode('utf-8', 'surrogatepass'))} "
                  f"bytes -- exceeds the {IDENTITY_HEADER_MAX_BYTES}-byte bound (design/"
                  f"FABLE-DISPATCH-MECHANICS-SPEC.md §1, the s65 house precedent). Refused "
                  f"before any kernel call -- never truncated, never passed through.")
    return v


def _parse_identity_headers(headers) -> tuple[str, str | None, dict[str, str] | None]:
    """The service-side half of the one identity conduit (spec §1/§2). Parses this request's
    identity headers into the closed three-case resolution `boundary_diagnostic_log.bind_identity`
    records: returns `(resolution_case, principal_id_or_None, vendor_stamp_dict_or_None)`.

    Raises `_IdentityRefusal` for an oversized (`_bounded_header` above) or MALFORMED value --
    a non-integer `x-autoharn-vendor-ts`, a vendor HMAC that is not 64 lowercase hex characters,
    or a minted-principal header that is not a non-negative integer within `[0, MAX_ID]` -- BEFORE
    any kernel call (spec §1, verbatim: "draws a typed, teaching refusal ... never truncation,
    never pass-through"). This function never verifies the HMAC's cryptographic validity (the
    conduit invariant, §1) -- only that the vendor-stamp headers are STRUCTURALLY the shape s17's
    own trigger expects; a structurally-valid-but-forged stamp is a kernel-side question,
    answered by `stamp_verified=false` (witnessed in this build's own report), never a
    service-side one.

    RESOLUTION ORDER (spec §2, closed three cases): minted-principal present -> ("minted", pid,
    vendor-dict-or-None -- vendor rides along to its own GUCs even when minted governs, spec §2:
    "the vendor stamp rides along to its own GUCs"); else vendor stamp present (all FOUR
    mandatory GUC-bearing headers -- session/agent/ts/hmac; invocation is optional, s23's own
    capture-only column) -> ("vendor", None, vendor-dict); else -> ("anonymous", None, None)."""
    minted_raw = _bounded_header(headers, IDENTITY_HEADER_MINTED_PRINCIPAL)
    principal_id: str | None = None
    if minted_raw is not None:
        try:
            pid_int = int(minted_raw)
        except ValueError:
            raise _IdentityRefusal(
                IDENTITY_HEADER_MINTED_PRINCIPAL,
                f"identity header {IDENTITY_HEADER_MINTED_PRINCIPAL!r} = {minted_raw!r} is not "
                f"an integer principal id.") from None
        if pid_int < 0 or pid_int > MAX_ID:
            raise _IdentityRefusal(
                IDENTITY_HEADER_MINTED_PRINCIPAL,
                f"identity header {IDENTITY_HEADER_MINTED_PRINCIPAL!r} = {pid_int} is outside "
                f"the id domain 0 <= id <= {MAX_ID} (A4.2's own bound, applied here too).")
        principal_id = str(pid_int)

    session = _bounded_header(headers, IDENTITY_HEADER_VENDOR_SESSION)
    agent = _bounded_header(headers, IDENTITY_HEADER_VENDOR_AGENT)
    ts_raw = _bounded_header(headers, IDENTITY_HEADER_VENDOR_TS)
    hmac_raw = _bounded_header(headers, IDENTITY_HEADER_VENDOR_HMAC)
    invocation = _bounded_header(headers, IDENTITY_HEADER_VENDOR_INVOCATION)

    vendor_present = {session, agent, ts_raw, hmac_raw} != {None}
    vendor_stamp: dict[str, str] | None = None
    if vendor_present:
        missing = [n for n, v in (
            (IDENTITY_HEADER_VENDOR_SESSION, session), (IDENTITY_HEADER_VENDOR_AGENT, agent),
            (IDENTITY_HEADER_VENDOR_TS, ts_raw), (IDENTITY_HEADER_VENDOR_HMAC, hmac_raw),
        ) if v is None]
        if missing:
            raise _IdentityRefusal(
                missing[0],
                f"a partial vendor stamp was presented -- {session and IDENTITY_HEADER_VENDOR_SESSION}, "
                f"missing required header(s) {missing} (all four of session/agent/ts/hmac are "
                f"mandatory together, spec §1/§2 -- a partial stamp is malformed, never "
                f"completed or silently dropped).")
        try:
            int(ts_raw)
        except ValueError:
            raise _IdentityRefusal(
                IDENTITY_HEADER_VENDOR_TS,
                f"identity header {IDENTITY_HEADER_VENDOR_TS!r} = {ts_raw!r} is not an integer "
                f"unix timestamp.") from None
        if not _VENDOR_HMAC_RE.match(hmac_raw):
            raise _IdentityRefusal(
                IDENTITY_HEADER_VENDOR_HMAC,
                f"identity header {IDENTITY_HEADER_VENDOR_HMAC!r} is not a 64-character lowercase "
                f"hex sha256 digest (the shape kernel/lineage/s17-stamp-mechanism.sql's own "
                f"stamp_valid expects) -- structurally malformed, refused before any kernel "
                f"call (this service never verifies the HMAC itself, only its shape).")
        vendor_stamp = {
            "vendor_session": session, "vendor_agent": agent, "vendor_ts": ts_raw,
            "vendor_hmac": hmac_raw,
        }
        if invocation is not None:
            vendor_stamp["vendor_invocation"] = invocation

    if principal_id is not None:
        return "minted", principal_id, vendor_stamp
    if vendor_stamp is not None:
        return "vendor", None, vendor_stamp
    return "anonymous", None, None


def _apply_minted_actor(payload: dict) -> JSONResponse | None:
    """design/FABLE-DISPATCH-MECHANICS-SPEC.md §2/§3, reshaped by the fresh-context review's
    CRITICAL (ledger row 1525): a MINTED-PRINCIPAL identity (resolution case "minted") sets this
    write's `actor` field from the conduit's own validated fact -- when the payload makes no
    competing claim. A payload whose OWN explicit `actor` disagrees with the minted header is a
    typed 409 `minted_actor_conflict`, refused BEFORE any kernel call -- never a silent
    override (spec §2's "declared, never silent"; the diagnostic log cannot carry the
    declaration because it is diagnostic-grade, never evidentiary). Agreement is compared on
    the exact-integer axis: a non-integer explicit `actor` (including a bool) under a minted
    header is a disagreement by construction, not coerced. The vendor stamp, if also present,
    still rides along to its own GUCs via `_psql`, entirely independent of this rule. Returns
    the refusal response, or None after (possibly) setting `payload['actor']` in place."""
    ctx = boundary_diagnostic_log.REQUEST_CONTEXT.get()
    if ctx is None or ctx.resolution_case != "minted" or ctx.principal is None:
        return None
    minted = int(ctx.principal)
    if "actor" in payload:
        claimed = payload["actor"]
        agrees = isinstance(claimed, int) and not isinstance(claimed, bool) and claimed == minted
        if not agrees:
            body = MintedActorConflict(
                minted_principal=minted,
                payload_actor=repr(claimed),
                message=(
                    f"this write's payload claims actor={claimed!r} while its own "
                    f"X-Autoharn-Minted-Principal header names principal {minted} -- two "
                    f"competing attribution claims on one write. Refused rather than silently "
                    f"resolved (design/FABLE-DISPATCH-MECHANICS-SPEC.md §2: identity resolution "
                    f"is declared, never silent): either drop the payload's `actor` field (the "
                    f"minted principal will be attributed), set it equal to the minted "
                    f"principal, or drop the minted-principal header. Nothing was written."),
            )
            boundary_diagnostic_log.log_event(
                boundary_diagnostic_log.Event.REFUSAL, disposition=body.disposition,
                minted_principal=minted)
            return JSONResponse(status_code=409, content=body.model_dump())
    payload["actor"] = minted
    return None


# IDENTITY_ENFORCEMENT (design/FABLE-DISPATCH-MECHANICS-SPEC.md §3, ledger row 1471 sub-item 4c
# "rung (a)"): the anonymous-write refusal's own posture, set ONCE at startup from the multiplex
# TOML (already validated against `boundary_multiplex_config.IDENTITY_ENFORCEMENT_POSTURES`) --
# mirrors `boundary_diagnostic_log.configure_level`'s own construction-time-defense-in-depth
# pattern exactly.
_identity_enforcement_posture = boundary_multiplex_config.DEFAULT_IDENTITY_ENFORCEMENT


def configure_identity_enforcement(posture: str) -> None:
    global _identity_enforcement_posture
    if posture not in boundary_multiplex_config.IDENTITY_ENFORCEMENT_POSTURES:
        raise ValueError(
            f"boundary_service: REFUSED -- configure_identity_enforcement({posture!r}) is not "
            f"one of {sorted(boundary_multiplex_config.IDENTITY_ENFORCEMENT_POSTURES)}.")
    _identity_enforcement_posture = posture


# The write-shaped routes the anonymous-write refusal (rung a) applies to -- every `/write/*`
# surface plus the dedicated `/artifacts` POST (Part B's own separate route, not routed through
# `/write/{surface}` -- see serving/README.md's own endpoint table). A GET is never
# authority-bearing (spec §3: "anonymous sessions keep NO write surface beyond journaled
# refusals" -- reads are not a write surface at all); the `/d/{deployment}` prefix is stripped
# before this check runs (this is a route-SHAPE test, not a deployment-specific one).
def _is_authority_bearing_write(method: str, path: str) -> bool:
    if method != "POST":
        return False
    # Strip the mandatory /d/{deployment} segment (multiplex spec §2) before the shape test --
    # e.g. "/d/autoharn1/write/ledger" -> "/write/ledger", "/d/autoharn1/artifacts" -> "/artifacts".
    parts = path.split("/", 3)
    rest = "/" + parts[3] if len(parts) > 3 else "/"
    return rest.startswith("/write/") or rest == "/artifacts"

# design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part B: `POST /d/{deployment}/artifacts`' own raw-
# body buffering bound. NOT a second, independent judgment of "is this artifact too large" (the
# spec's own P1 instruction: "kernel hash-verification is the refusal authority; no second size
# limit") -- kernel.artifact_write's own 1 MiB cap is the ONE authority on artifact size, and
# this constant is DERIVED from it, never chosen independently (see serving/bounds.py's own
# docstring for the base64-inflation derivation and the kernel citation).


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


class DeploymentCallSaturated(Exception):
    """Multiplex spec §4: raised by `_psql` -- the SAME shared choke point `KernelCallSaturated`
    is raised from -- when the CALLING deployment's OWN `dep_semaphore`
    (`MAX_INFLIGHT_PER_DEPLOYMENT` slots) is exhausted, distinct from the GLOBAL bound
    `KernelCallSaturated` guards. Checked FIRST (before the global gate): a deployment that has
    already saturated its own sub-bound is refused on ITS OWN label without ever touching the
    global gate's accounting, so the two conditions -- 'this deployment is at capacity' vs 'the
    whole server is at capacity' -- can never be conflated under one label (spec §4/A6/A8's
    label-honesty ruling, extended to the new axis). Raised BEFORE `subprocess.run` is ever
    invoked, exactly like `KernelCallSaturated` -- an ordinary, expected, load-driven condition,
    never logged server-side (nothing a log would explain the typed response does not already
    say)."""


class BoundaryConfig:
    """This deployment's resolved (db, host, schema, kern, role) plus the psql connection
    host -- kept distinct from the LEDGER's own `host` field on purpose: `deployment.json`'s
    `host` is the POSTGRES host (what `led`/`judge` already call `--host`), never this HTTP
    service's own bind address (spec §2's separate `--host`/`--port` argv).

    MULTIPLEX SPEC §4: as of the multiplex build, every `BoundaryConfig` also carries its OWN
    `dep_semaphore` -- a `threading.BoundedSemaphore` sized to `dep_limit`
    (`MAX_INFLIGHT_PER_DEPLOYMENT`, computed once at process startup by
    `compute_per_deployment_limit`) -- so `_psql` can gate a kernel call on BOTH the global
    bound (`_KERNEL_CALL_SEMAPHORE`) and this deployment's own sub-bound without a second
    dict/lookup at the choke point. `record.name` is REQUIRED here (never `None`): every
    multiplexed deployment is named, by construction (the TOML table key, spec §3)."""

    def __init__(
        self,
        record: deployment_record.DeploymentRecord,
        dep_semaphore: threading.BoundedSemaphore | None = None,
        dep_limit: int | None = None,
    ) -> None:
        for field_name in ("schema", "kern", "role"):
            value = getattr(record, field_name)
            if not _IDENT_RE.match(value):
                raise SystemExit(
                    f"boundary_service: REFUSED at start-up -- deployment config field "
                    f"'{field_name}'={value!r} is not a plain SQL identifier "
                    f"(pattern {_IDENT_RE.pattern}). A deployment record is operator-authored "
                    f"config, not HTTP input, but this service still refuses to interpolate an "
                    f"unvalidated identifier into SQL text (ADR-0002 rung 1, construction-time)."
                )
        self.record = record
        # Multiplex spec §4: a deployment with no explicit sub-bound wired (unused outside this
        # module's own unit-shaped call sites, e.g. W12's in-process route-table witness, which
        # builds a BoundaryConfig without ever calling _psql) gets a permissive default rather
        # than a zero-capacity semaphore that would wedge on its very first acquire.
        self.dep_limit = dep_limit if dep_limit is not None else MAX_INFLIGHT_KERNEL_CALLS
        self.dep_semaphore = dep_semaphore if dep_semaphore is not None else threading.BoundedSemaphore(self.dep_limit)

    @property
    def name(self) -> str:
        assert self.record.name is not None  # multiplex spec §3: every deployment is named by construction
        return self.record.name

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

    MULTIPLEX SPEC §4's admission axis, a SECOND independent gate ahead of the global one: this
    function first acquires a NON-BLOCKING slot from `cfg.dep_semaphore`
    (`MAX_INFLIGHT_PER_DEPLOYMENT`, `cfg`'s own sub-bound). Checked BEFORE the global gate --
    a deployment already at its own capacity is refused on its own label
    (`DeploymentCallSaturated`) without ever touching the global gate's accounting, so a caller
    can always tell "my deployment is busy" from "the whole server is busy" (spec §4's
    distinct-label requirement). Only once BOTH gates admit the call does `subprocess.run` run;
    both slots release together in the `finally` below (reached only when both were actually
    acquired -- either saturation raise returns before this `try` is ever entered, so there is
    no double-release to guard against on that path).

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
    preamble = f"SET ROLE {cfg.role};\nSET search_path = {cfg.schema}, {cfg.kern};\n"
    # design/FABLE-DISPATCH-MECHANICS-SPEC.md §1: the vendor stamp's own five GUCs, threaded
    # into THIS request's per-request psql session -- the SAME GUCs kernel/lineage/
    # s17-stamp-mechanism.sql's set_stamp trigger and s23-per-invocation-stamp-token.sql already
    # read via current_setting(..., true). `-v` bound vars (never string-spliced -- this
    # module's own house convention, matching every other injection-safe substitution here),
    # SET on this connection ONLY (a fresh psql subprocess per call, never the server's own
    # environment -- the exact confusion ledger row 1467 witnessed). A request with no vendor
    # stamp (the ordinary, unstamped case) adds nothing here -- set_stamp's own
    # current_setting(..., true) reads NULL for every app.vendor_* GUC exactly as it always has,
    # landing stamp_verified=false, unchanged from this build's predecessor.
    ctx = boundary_diagnostic_log.REQUEST_CONTEXT.get()
    if ctx is not None and ctx.vendor_stamp:
        for guc, val in ctx.vendor_stamp.items():
            var = f"_identity_{guc}"
            args += ["-v", f"{var}={val}"]
            preamble += f"SET app.{guc} = :'{var}';\n"
    args += ["-f", "/dev/stdin"]
    env = dict(os.environ)
    env["PGCONNECT_TIMEOUT"] = str(PSQL_CONNECT_TIMEOUT_S)
    # Multiplex spec §4: the PER-DEPLOYMENT gate first -- a deployment already at its own
    # capacity is refused on its own label, never touching the global gate's accounting.
    if not cfg.dep_semaphore.acquire(blocking=False):
        raise DeploymentCallSaturated(
            f"deployment {cfg.name!r} already has MAX_INFLIGHT_PER_DEPLOYMENT={cfg.dep_limit} "
            f"concurrent kernel calls in flight (multiplex spec §4) -- this call is refused "
            f"immediately rather than queued. The cause is ordinary concurrent load on THIS "
            f"deployment, not a defect in this request nor a whole-server condition; the "
            f"correct response is to retry after a short backoff."
        )
    if not _KERNEL_CALL_SEMAPHORE.acquire(blocking=False):
        cfg.dep_semaphore.release()
        raise KernelCallSaturated(
            f"the service already has MAX_INFLIGHT_KERNEL_CALLS={MAX_INFLIGHT_KERNEL_CALLS} "
            f"concurrent kernel calls in flight (spec A9) -- this call is refused immediately "
            f"rather than queued. The cause is ordinary concurrent load, not a defect in this "
            f"request; the correct response is to retry after a short backoff."
        )
    # Diagnostic-logging spec §5 emission site (b), `_psql`'s single chokepoint: `kernel_call`
    # is emitted exactly once per subprocess.run outcome below (success or one of the three
    # exception legs) -- never for a saturation refusal above (KernelCallSaturated/
    # DeploymentCallSaturated are refused BEFORE subprocess.run ever runs; those are `refusal`
    # events, emitted by the app's own exception handlers, not a kernel call that happened).
    # `route` is the current request's own route (`current_route()`, `None`/"unknown" outside
    # any request context -- this project's own fixture bank calls `_psql`/`_query_json`
    # directly, unit-style, with no HTTP request in flight) -- deliberately NOT a new parameter
    # threaded through every one of this function's callers (ADR-0004: minimal-touch). Fresh-
    # context review finding (a), post-f450019: this field used to be named `surface`, which
    # `write_verdict`'s own field ALSO uses for a different shape (the short write-surface
    # label, e.g. "ledger") -- one name, two shapes, silently splitting a `jq` query keyed on
    # `surface` across events. Renamed to `route` here, which is exactly what this field
    # already meant, and matches the SAME field's shape on `request_start`/`request_end`
    # (see boundary_diagnostic_log.py's own EVENT_REQUIRED_FIELDS comment, "ONE SHAPE PER
    # FIELD NAME, EVERYWHERE").
    _kernel_call_started = time.monotonic()
    try:
        cp = subprocess.run(
            args, input=preamble + script, capture_output=True, text=True,
            env=env, timeout=PSQL_EXEC_TIMEOUT_S,
        )
        boundary_diagnostic_log.log_event(
            boundary_diagnostic_log.Event.KERNEL_CALL,
            route=boundary_diagnostic_log.current_route() or "unknown",
            exit_class=_psql_exit_class(cp.returncode),
            duration_ms=(time.monotonic() - _kernel_call_started) * 1000,
        )
        return cp
    except subprocess.TimeoutExpired as e:
        boundary_diagnostic_log.log_event(
            boundary_diagnostic_log.Event.KERNEL_CALL,
            route=boundary_diagnostic_log.current_route() or "unknown",
            exit_class="infra", duration_ms=(time.monotonic() - _kernel_call_started) * 1000,
        )
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
        boundary_diagnostic_log.log_event(
            boundary_diagnostic_log.Event.KERNEL_CALL,
            route=boundary_diagnostic_log.current_route() or "unknown",
            exit_class="unclassified", duration_ms=(time.monotonic() - _kernel_call_started) * 1000,
        )
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
        boundary_diagnostic_log.log_event(
            boundary_diagnostic_log.Event.KERNEL_CALL,
            route=boundary_diagnostic_log.current_route() or "unknown",
            exit_class="unclassified", duration_ms=(time.monotonic() - _kernel_call_started) * 1000,
        )
        raise PsqlUnclassifiedFailure(
            f"psql subprocess could not be launched (ValueError before any connection was "
            f"attempted -- e.g. an embedded NUL byte in an argument this function's own "
            f"representability gates should have refused upstream): {e}"
        ) from e
    finally:
        # A9 + multiplex spec §4: released as early as honesty allows -- the instant
        # subprocess.run itself returns or raises, on EVERY exit path (success and both
        # exception paths above alike). Only reached when BOTH slots were actually acquired
        # (either saturation raise above returns before entering this try/finally at all, so
        # there is no double-release to guard against). Release order (global then
        # per-deployment) is the exact reverse of acquisition order.
        _KERNEL_CALL_SEMAPHORE.release()
        cfg.dep_semaphore.release()


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
    _classify_psql_exit(cp)
    lines = [ln for ln in cp.stdout.splitlines() if ln.strip()]
    if not lines:
        return None
    return json.loads(lines[-1])


def _query_json_stdin_var(cfg: BoundaryConfig, var_name: str, file_path: str, sql: str) -> Any:
    """design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part B's sibling to `_query_json` above, for a
    payload too large to cross as a psql `-v` execve argument (kernel/lineage/
    s51-artifact-store.sql's OWN header: "never a command-line `-v` argument for this payload...
    MAX_ARG_STRLEN caps any ONE execve argument, and a 1 MiB artifact base64s to ~1.4 MiB").
    Mirrors seen-red/s51-artifact-store/run_fixtures.py's own `kernel_write_large` transport
    exactly: `\\set <var_name> \\`cat '<file_path>'\\`` -- psql's backtick-command value carrier
    loads the file's content into a psql variable via a PIPE READ, never an execve argument, so
    no MAX_ARG_STRLEN wall applies. `file_path` is ALWAYS this service's own tempfile (never
    caller-controlled text spliced into SQL), so this is the same trust boundary `_psql`'s own
    schema/kern/role interpolation already relies on (ADR-0002 rung 1), not a new one. Same
    exit-code fidelity as `_query_json` (`_classify_psql_exit`)."""
    script = f"\\set {var_name} `cat '{file_path}'`\n{sql}"
    cp = _psql(cfg, script)
    _classify_psql_exit(cp)
    lines = [ln for ln in cp.stdout.splitlines() if ln.strip()]
    if not lines:
        return None
    return json.loads(lines[-1])


def _psql_exit_class(returncode: int) -> str:
    """The success/infra/unclassified three-way split over a psql exit code, named ONCE
    (ADR-0012 P1) -- `_classify_psql_exit` below (which RAISES on the two non-success classes)
    and the diagnostic-logging spec's `kernel_call` event (`_psql`, which only LABELS the
    outcome, never raises on its account -- the log layer must never itself become a second,
    raising validator, design/FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md's standing line) both
    consult this ONE pure classifier rather than each independently re-deriving the
    returncode -> class mapping (a hazard this build found in passing while touching this exact
    function for the log event's own needs, per CLAUDE.md's engineering-responsibility rule --
    a second, drifting copy of "exit 2 is infra, else nonzero is unclassified" would have been
    exactly the class this project's own house style forbids)."""
    if returncode == 2:
        return "infra"
    if returncode != 0:
        return "unclassified"
    return "success"


def _classify_psql_exit(cp: subprocess.CompletedProcess[str]) -> None:
    """A4.3's exit-code fidelity, factored out (ADR-0012 P1) so `_lineage_head` below -- the
    design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md /meta route's own detect-query runner, which needs
    the SAME exit-2-vs-other classification `_query_json` already applies but does NOT want
    `_query_json`'s `json.loads` (a `.detect.sql` file prints a bare `t`/`f`, not JSON) -- can
    share the ONE classification rule rather than re-deriving it. Raises `PsqlInfraFailure` on
    exit 2 (connection-level), `PsqlUnclassifiedFailure` on any other nonzero exit; returns None
    (the caller proceeds) on exit 0. Behavior-preserving extraction from `_query_json`'s own
    pre-existing inline checks -- no classification changes; as of the diagnostic-logging build
    this reuses `_psql_exit_class` for the returncode -> class judgment rather than repeating the
    `== 2` / `!= 0` tests inline a second time."""
    cls = _psql_exit_class(cp.returncode)
    if cls == "infra":
        raise PsqlInfraFailure(f"psql query failed (exit {cp.returncode}, connection-level): {cp.stderr.strip()[-2000:]}")
    if cls == "unclassified":
        raise PsqlUnclassifiedFailure(
            f"psql query failed (exit {cp.returncode}, NOT connection-level -- a script/data-"
            f"level residue A4.1/A4.2's closures should have made unreachable via an ordinary "
            f"request; this is a boundary or deployment defect, not a request defect): "
            f"{cp.stderr.strip()[-2000:]}")


def _lineage_head(cfg: BoundaryConfig) -> str | None:
    """design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md's /meta route, mechanism item 3: "the
    deployment's kernel lineage head". Walks `bootstrap/migrate_core.py`'s OWN ordered manifest
    (`_manifest()`, derived from the kernel/lineage/ directory via bootstrap/lineage_manifest.py
    -- reused, not re-derived, ADR-0012 P1) and runs each entry's `kernel/lineage/<name>.detect.sql` sibling IN
    ORDER, returning the LAST entry (basename minus `.sql`) whose detect confirmed `t`, stopping
    at the first non-`t` result (or the first manifest entry with no `.detect.sql` sibling at
    all -- a lineage-authoring defect this route has no business turning into a 500 for; it just
    stops the walk there, same as an ordinary "not yet applied" entry).

    DELIBERATE DEPARTURE from migrate_core.py's own per-entry runner (`_run_detect`,
    `_current_head_and_missing`): each detect query here runs through THIS module's OWN `_psql`
    -- the one disciplined transport every other call in this service already uses
    (PSQL_CONNECT_TIMEOUT_S/PSQL_EXEC_TIMEOUT_S bounds, the global+per-deployment admission
    semaphores) -- rather than migrate_core's own bare `subprocess.run` (untimed beyond its own
    60s literal, and NOT admission-gated against this service's shared kernel-call bound).
    Importing and calling migrate_core's own DB-touching runner here would silently reopen
    exactly the kind of unbounded, ungated live-DB call path this service's whole design exists
    to close (CLAUDE.md's hazard-in-reach rule) -- only the manifest (pure text parsing, no DB
    call) is reused; the DB-touching half is reimplemented against `_psql` instead. Exit-code
    fidelity matches `_query_json`'s own (`_classify_psql_exit`): a genuine connection failure
    still raises the SAME typed `infra_failure`/`unclassified_failure` this whole service already
    uses everywhere else, rather than being silently swallowed into "no lineage head detected".

    FLAGGED CHOICE (ADR-0000 2(a)): for a fully up-to-date world this walks EVERY manifest entry
    (currently ~50) sequentially, one psql subprocess each -- no caching (spec §5's own
    no-caching discipline, applied here too), so a slow /meta is the honest, disclosed cost of a
    live-detected fact rather than a stored version literal that could drift from reality."""
    try:
        manifest = migrate_core._manifest()
    except migrate_core.MigrateRefusal:
        return None
    head: str | None = None
    for name in manifest:
        stem = name[:-4] if name.endswith(".sql") else name
        detect_path = migrate_core.LINEAGE_DIR / f"{stem}.detect.sql"
        if not detect_path.is_file():
            break
        script = detect_path.read_text(encoding="utf-8")
        cp = _psql(cfg, script, extra_v={"schema": cfg.schema, "kern": cfg.kern, "role": cfg.role})
        _classify_psql_exit(cp)
        lines = [ln.strip() for ln in cp.stdout.splitlines() if ln.strip()]
        if not lines or not all(ln == "t" for ln in lines):
            break
        head = stem
    return head


# boundary-verdict-read-surface (row 221): the two-trust-roots section (serving/README.md)'s own
# verdicts-not-instruments rule, applied to a FILESYSTEM read this service has never needed
# before -- judge/verify-chain/doctor are the deliberately-outside-the-boundary "independent
# instruments" group (README's own words); this route serves their LATEST BANKED RESULT, never
# runs one. `_REPO_ROOT` is this module's own repo checkout root (two directories up from
# serving/) -- the SAME relative-path convention `sys.path.insert` above already establishes.
_REPO_ROOT = Path(__file__).resolve().parent.parent
# AUTOHARN_JUDGE_DERIVATIONS_ROOT (test-only escape hatch, read ONCE at import time): the
# fixture's own seam for witnessing BOTH polarities (a scratch dir with a planted
# `derivation.json`; an empty scratch dir with none) against a SEPARATE server SUBPROCESS
# (`configure_judge_derivations_root` below is same-process only -- a fixture that spawns this
# module as its own subprocess, as every seen-red suite here does, needs an env-var seam
# instead; the SAME class of test-only override this repo's own `pghost_resolve.py` env-var
# convention already establishes for a different constant). Unset in ordinary operation -- the
# real bank is the real bank in production.
_DEFAULT_JUDGE_DERIVATIONS_ROOT = (
    Path(os.environ["AUTOHARN_JUDGE_DERIVATIONS_ROOT"])
    if os.environ.get("AUTOHARN_JUDGE_DERIVATIONS_ROOT")
    else _REPO_ROOT / "engine" / "docs" / "ledger-marriage" / "derivations")
# The FOUR sibling differential families' own RETENTION roots nest INSIDE the bare `ledger`
# root as subdirectories (engine/contemp_differential.py, engine/ordering_differential.py,
# engine/preamble_differential.py, engine/review_gap_differential.py all set their own
# `RETENTION = <bare-root> / "<subtree-name>"`; engine/ledger_differential.py's own `RETENTION`
# IS the bare root) -- they are NOT sibling directories of the bare root, they are UNDER it. Named
# here ONCE (ADR-0012 P1); if a future differential module adds a sixth family this tuple is the
# one place to extend.
#
# TWO DISCLOSED LIMITS (round-2 re-review MINORs, autoharn3 row 369): (1) a derivation
# under a subtree NOT in the tuple above falls back to domain='ledger' -- a GUESS, honest
# only while the family universe stays the closed five; extending the tuple is mandatory
# with any sixth family, or the guess becomes round-1's confident-mislabel reborn. (2) an
# exact-mtime tie between two distinct files resolves by filesystem enumeration order --
# undisclosed-nondeterminism accepted because a tie now requires two distinct files
# sharing an mtime (the one-pass scan removed round 1's guaranteed duplicate case).
#
# FIX ROUND (focused re-review CRITICAL, reviewer witnessed over real HTTP: a contemporaneity-
# stored DIVERGE_DEFECT reported as domain 'ledger'): the FIRST cut of this scan iterated a
# `{domain: root}` dict and called `root.rglob("derivation.json")` PER DOMAIN -- since the bare
# root physically CONTAINS the four subtrees, the 'ledger' domain's own scan re-discovered every
# file already reachable through its true subtree, and (dict order + a strict `>` mtime
# tiebreak) whichever domain's scan reached a given file'S mtime FIRST won the attribution --
# 'ledger' iterates first, so it always won ties against the correct subtree domain for any file
# genuinely stored under one, regardless of which subtree it actually lived in. Domain must be a
# structural fact about WHERE THE FILE IS, never a side effect of scan order -- fixed by scanning
# the bare root EXACTLY ONCE and deriving each file's domain from its own path relative to that
# root (the file's first path component if it names one of the four known subtrees, else
# 'ledger' -- a file directly under the bare root, or under a `<target>/<ts>_<hash>/` pair that
# is not one of the four named subtrees, is genuinely `ledger_differential.py`'s own domain).
_JUDGE_DERIVATION_SUBTREES: tuple[str, ...] = (
    "contemporaneity", "ordering-violations", "preamble-ordering", "review-gap-audit",
)
_judge_derivations_root: Path = _DEFAULT_JUDGE_DERIVATIONS_ROOT


def configure_judge_derivations_root(path: Path) -> None:
    """Construction-time-defense-in-depth (the SAME pattern `configure_identity_enforcement`
    above already uses): overrides `_judge_derivations_root` wholesale -- the fixture's own seam
    for witnessing BOTH polarities (a scratch dir with a planted `derivation.json`; an empty
    scratch dir with none) without touching this checkout's own real, accumulating derivation
    bank. Never called in ordinary operation (`main` below leaves the default in place unless a
    future CLI flag is added -- none is, this build: the real bank IS the real bank in
    production)."""
    global _judge_derivations_root
    _judge_derivations_root = path


def _latest_judge_derivation() -> dict[str, Any] | None:
    """Scans every `derivation.json` under `_judge_derivations_root` (recursively, ONE pass --
    the bare root already contains every one of the four sibling subtrees, `_JUDGE_DERIVATION_
    SUBTREES`'s own leading comment), returns the one with the LATEST file mtime (never the
    lexicographically-last path -- a `--retain` run's own directory name embeds ITS run
    timestamp, not necessarily this scan's notion of "most recent on disk", though in practice
    the two agree; mtime is the honest, direct fact). DOMAIN ATTRIBUTION is derived from the
    matched file's own path, relative to the root -- its first path component if that names one
    of the four known subtrees, else 'ledger' -- NEVER from which domain's scan iteration
    happened to reach it first (the fix-round CRITICAL this docstring's leading comment names).
    Returns `None` if no `derivation.json` exists anywhere under the root -- read-only, no error
    on an absent/empty tree (a fresh checkout that has never run `judge --retain` is the ordinary
    case for the LIBRARY's own bare CLI, though NOT for this repo's own `./autoharn judge`
    wrapper -- see `NoBankedArtifact`'s own teach-text, corrected in the same fix round, for why
    that distinction matters). A malformed `derivation.json` (unparseable JSON, or missing an
    expected key) is SKIPPED, not raised -- this route degrades to the next-most-recent valid
    record, or to `None`, rather than 500ing the whole read surface over one corrupt retained
    artifact; ADR-0002's loudness is still honored server-side (the server's own log records
    which files were skipped, `_log_infra_failure`'s own house channel is not it -- see the
    route's own body)."""
    root = _judge_derivations_root
    if not root.is_dir():
        return None
    best: tuple[float, str, dict[str, Any]] | None = None  # (mtime, domain, parsed)
    skipped: list[str] = []
    for path in root.rglob("derivation.json"):
        try:
            mtime = path.stat().st_mtime
            parsed = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(parsed, dict) or "target" not in parsed or "verdict" not in parsed:
                skipped.append(str(path))
                continue
        except (OSError, ValueError):
            skipped.append(str(path))
            continue
        rel_parts = path.relative_to(root).parts
        domain = rel_parts[0] if rel_parts and rel_parts[0] in _JUDGE_DERIVATION_SUBTREES else "ledger"
        if best is None or mtime > best[0]:
            best = (mtime, domain, parsed)
    if skipped:
        print(f"boundary_service: _latest_judge_derivation skipped {len(skipped)} unreadable/"
              f"malformed derivation.json path(s): {skipped}", file=sys.stderr)
    if best is None:
        return None
    mtime, domain, parsed = best
    asp_record = parsed.get("asp_record") or {}
    sql_record = parsed.get("sql_record") or {}
    return {
        "domain": domain,
        "target": parsed.get("target", ""),
        "verdict": parsed.get("verdict", ""),
        "asp_input_hash": asp_record.get("input_hash"),
        "sql_input_hash": sql_record.get("input_hash"),
        "computed_at": asp_record.get("ts") or sql_record.get("ts") or "",
        "banked_at": datetime.datetime.fromtimestamp(
            mtime, tz=datetime.timezone.utc).isoformat(),
    }


def _kind_vocabulary(cfg: BoundaryConfig) -> list[str]:
    """`GET /d/{deployment}/kinds` (ledger row 1480, restoring the legacy direct-psql `led`'s own
    `_led_kind_refusal_teach` re-query -- see that function's own comment, bootstrap/templates/
    legacy-led.tmpl at the pre-retirement commit 1ddb66a, for the query this mirrors exactly): the
    kernel's `ledger_kind_check` CHECK constraint on `{cfg.schema}.ledger`, read back via
    `pg_get_constraintdef` and parsed with the SAME `regexp_matches(..., '''([a-z_]+)''::text',
    'g')` pattern the legacy tool used -- never a hardcoded Python-side copy of the vocabulary
    (s22/s25 have each additively widened this constraint once already; a literal list here would
    silently drift out of sync with the next such delta, exactly the class the legacy tool's own
    comment names as the reason it re-queries live rather than hand-maintaining a second copy).

    `WITH ORDINALITY` + `array_agg(... ORDER BY ord)` preserves the constraint text's own member
    order (the same order the legacy tool's `string_agg` produced) -- this is a presentation
    nicety, not a semantic one (CHECK ... IN (...) membership has no order), but a stable,
    reproducible order over an arbitrary one is the honest smaller choice.

    Returns an EMPTY list if no constraint named exactly `ledger_kind_check` is found on
    `{cfg.schema}.ledger` -- not an error: `ledger_kind_check` has carried this exact name since
    s15 (Postgres's own default naming for a single-column CHECK, `<table>_<column>_check`,
    already produces it un-renamed), so every world this service could possibly be pointed at
    carries it; an empty result names a genuinely unexpected deployment shape rather than
    manufacturing a capability-absent refusal for a constraint that is, in practice, always
    present. The caller (this route's own handler) reports the empty list as-is; a rebased CLI
    shim's own re-teach helper (serving/boundary_cli_client.py) treats an empty list as "could
    not determine the vocabulary" and says so honestly rather than printing a teach block with
    nothing in it."""
    rows = _query_json(
        cfg,
        f"SELECT coalesce(jsonb_agg(t.k ORDER BY t.ord), '[]'::jsonb) FROM "
        f"(SELECT m.k[1] AS k, m.ord FROM pg_catalog.pg_constraint con "
        f"JOIN pg_catalog.pg_class rel ON rel.oid = con.conrelid "
        f"JOIN pg_catalog.pg_namespace ns ON ns.oid = rel.relnamespace "
        f"CROSS JOIN LATERAL regexp_matches(pg_get_constraintdef(con.oid), "
        f"'''([a-z_]+)''::text', 'g') WITH ORDINALITY AS m(k, ord) "
        f"WHERE con.conname = 'ledger_kind_check' AND con.contype = 'c' "
        f"AND ns.nspname = '{cfg.schema}' AND rel.relname = 'ledger') t;",
    )
    return list(rows) if isinstance(rows, list) else []


def _regclass_exists(cfg: BoundaryConfig, qualified_name: str) -> bool:
    out = _query_json(cfg, f"SELECT to_jsonb(to_regclass('{qualified_name}') IS NOT NULL);")
    return bool(out)


def _column_exists(cfg: BoundaryConfig, schema: str, table: str, column: str) -> bool:
    """design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md's `/views/{view}` route: object existence
    alone (`_regclass_exists`) is NOT sufficient capability detection for a view whose NAME is
    stable across lineage deltas but whose COLUMN SHAPE is not -- `work_item_violations` is the
    live example (its `target_id` column arrived at s37; a pre-s37 world still carries a view
    NAMED `work_item_violations`, just without that column, live-witnessed against this repo's
    own `autoharn1` world, whose lineage head is s30: the pre-column-check code reached a bare
    `column "target_id" does not exist` SQL error, typed only as far as `unclassified_failure`
    -- accurate, but a worse signal than the SAME "object existence, never version literal"
    discipline this file already applies one level up. This closes that gap at the SAME
    granularity: does `{schema}.{table}` carry `{column}`, checked via
    `information_schema.columns` (never a version literal, matching `_regclass_exists`'s own
    discipline)."""
    out = _query_json(
        cfg,
        f"SELECT to_jsonb(EXISTS (SELECT 1 FROM information_schema.columns "
        f"WHERE table_schema = '{schema}' AND table_name = '{table}' "
        f"AND column_name = '{column}'));")
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
    # legacy-led-retirement inventory pass (ledger row 1149): the ONE fact `has_s45_standing_
    # lifecycle()` (bootstrap/templates/legacy-led.tmpl) probes -- the widened
    # principal_binding_active_kind_shape CHECK naming principal_standing_declared, a fact
    # only s45's re-issue produces (kernel/lineage/s45-standing-lifecycle.detect.sql fact 1 of
    # 4; the single fact is sufficient here exactly as it is for legacy's own probe -- the
    # detect file's other three facts exist for the detect ceremony's OWN thoroughness, not
    # because any one alone is ambiguous).
    s45 = bool(_query_json(
        cfg,
        f"SELECT to_jsonb(EXISTS (SELECT 1 FROM pg_constraint con "
        f"JOIN pg_class rel ON rel.oid = con.conrelid "
        f"JOIN pg_namespace ns ON ns.oid = rel.relnamespace "
        f"WHERE ns.nspname = '{cfg.schema}' AND rel.relname = 'ledger' AND con.contype = 'c' "
        f"AND con.conname = 'principal_binding_active_kind_shape' "
        f"AND pg_get_constraintdef(con.oid) LIKE '%principal_standing_declared%'));",
    ))
    # Row 173: extend the manifest past s45 (object-existence detection, the SAME
    # migrate-detect-drift discipline as every fact above -- see CapabilityManifest's own field
    # docstrings in boundary_models.py for why THESE four and not every intervening delta).
    s58_missives = _regclass_exists(cfg, f"{cfg.schema}.missive_open_threads")
    s60_entitlement = _column_exists(cfg, cfg.schema, "ledger", "entitlement_act_class")
    s61_signatures = _regclass_exists(cfg, f"{cfg.schema}.signed_commissions")
    s64_delegation = _column_exists(cfg, cfg.schema, "ledger", "delegation_redelegate_depth")
    return CapabilityManifest(s22_work=s22, s41_identity=s41, s43_boundary=s43,
                               credited_view=credited, s45_standing_lifecycle=s45,
                               s58_missives=s58_missives, s60_entitlement=s60_entitlement,
                               s61_signatures=s61_signatures, s64_delegation=s64_delegation)


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
    boundary_diagnostic_log.log_event(
        boundary_diagnostic_log.Event.REFUSAL, disposition=body.disposition, capability=capability)
    return JSONResponse(status_code=409, content=body.model_dump())


def payload_too_large(limit_bytes: int, observed_bytes: int, message: str) -> JSONResponse:
    """A2.2: the one typed shape both write-ingress size checkpoints return (ADR-0012 P1).
    As of A8 the two checkpoints carry two DIFFERENT bounds (MAX_WRITE_BODY_BYTES raw-body
    buffering; MAX_PSQL_ARG_BYTES re-serialized transport), so `limit_bytes` is supplied by
    the checkpoint that refused -- the shape stays one, and its numbers stay honest about
    which bound actually fired."""
    body = PayloadTooLarge(limit_bytes=limit_bytes, observed_bytes=observed_bytes, message=message)
    boundary_diagnostic_log.log_event(
        boundary_diagnostic_log.Event.REFUSAL, disposition=body.disposition,
        limit_bytes=limit_bytes, observed_bytes=observed_bytes)
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
    boundary_diagnostic_log.log_event(boundary_diagnostic_log.Event.REFUSAL, disposition=body.disposition)
    return JSONResponse(status_code=503, content=body.model_dump())


def deployment_saturated(deployment: str, inflight_limit: int, message: str) -> JSONResponse:
    """Multiplex spec §4: the one typed shape a deployment's OWN `MAX_INFLIGHT_PER_DEPLOYMENT`
    sub-bound, already exhausted, returns -- HTTP 503, distinct label from `server_saturated`
    (A6/A8's label-honesty ruling, extended to the new axis): this deployment is busy, which is
    NOT the same fact as the whole server being busy."""
    body = DeploymentSaturated(deployment=deployment, inflight_limit=inflight_limit, message=message)
    boundary_diagnostic_log.log_event(
        boundary_diagnostic_log.Event.REFUSAL, disposition=body.disposition, deployment=deployment)
    return JSONResponse(status_code=503, content=body.model_dump())


def unknown_deployment(known: list[str], deployment: str) -> JSONResponse:
    """Multiplex spec §2: the ONE typed 404 shape every `/d/{deployment}/...` route returns when
    `deployment` is not a key of the loaded config -- a closed enumeration fixed at startup.
    Names the full known set so a caller can self-correct without a second round trip."""
    body = UnknownDeployment(
        known=sorted(known),
        message=f"no deployment named {deployment!r} is configured on this service "
                f"(spec §2: the {{deployment}} discriminator is a closed enumeration fixed at "
                f"startup); known deployments: {sorted(known)}",
    )
    boundary_diagnostic_log.log_event(boundary_diagnostic_log.Event.REFUSAL, disposition=body.disposition)
    return JSONResponse(status_code=404, content=body.model_dump())


def unknown_view(view: str) -> JSONResponse:
    """design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md: the ONE typed 404 shape
    `GET /d/{deployment}/views/{view}` returns when `view` is not a key of `VIEW_REGISTRY` -- a
    closed enumeration fixed at authoring time (mirrors `unknown_deployment` above, ADR-0012 P1:
    the same shape, applied to a second discriminator). Names the full known set so a caller can
    self-correct without a second round trip; nothing is queried first."""
    body = UnknownView(
        known=sorted(VIEW_REGISTRY),
        message=f"no view named {view!r} is served by this boundary (design/"
                f"FABLE-BOUNDARY-READ-SURFACE-SPEC.md: the {{view}} discriminator is a closed, "
                f"spec-enumerated allowlist); known views: {sorted(VIEW_REGISTRY)}",
    )
    boundary_diagnostic_log.log_event(boundary_diagnostic_log.Event.REFUSAL, disposition=body.disposition)
    return JSONResponse(status_code=404, content=body.model_dump())


def _resolve_deployment(
    configs: dict[str, BoundaryConfig], deployment: str
) -> tuple[BoundaryConfig | None, JSONResponse | None]:
    """Multiplex spec §2: the ONE place every route resolves its `{deployment}` path segment
    against the loaded config (ADR-0012 P1 -- not re-derived per route). Returns
    `(cfg, None)` on a known deployment, `(None, <typed 404>)` otherwise -- the caller returns
    the second element immediately when it is not None.

    Diagnostic-logging spec §2 L1: this is also the ONE place `boundary_diagnostic_log.
    bind_deployment` is called -- every route already routes through here to resolve its
    `{deployment}` segment, so binding the resolved name onto the current request's own
    `RequestContext` here (rather than once per route handler) keeps this a single call site,
    not twenty (ADR-0012 P1)."""
    cfg = configs.get(deployment)
    if cfg is None:
        return None, unknown_deployment(list(configs.keys()), deployment)
    boundary_diagnostic_log.bind_deployment(cfg.name)
    return cfg, None


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


def _strict_bool_flag(name: str, value: str) -> tuple[bool, JSONResponse | None]:
    """Ledger row 154 (bulk superseded read): the ONE strict-boolean query-flag parser, named
    once (ADR-0012 P1) for `include_superseded` and any future opt-in flag on this shape. FastAPI's
    own `bool` query-param coercion is NOT used here on purpose -- it accepts a wide, undisclosed
    spelling set ("1"/"yes"/"on"/"True"/...), which is exactly the silent-default risk the
    commission's own text forbids ("anything but the exact typed values is the boundary's
    existing 422 shape, never a silent default"). The closed, exact vocabulary is `""` (the
    parameter omitted -- the pre-existing, unchanged default) and the two literal spellings
    `"true"`/`"false"`; anything else is a typed 422 naming the closed vocabulary, never a guess.
    Returns `(flag_value, None)` on a legal spelling, or `(False, <422 JSONResponse>)` on an
    illegal one (the caller returns the response and never reaches the flag_value)."""
    if value == "":
        return False, None
    if value == "true":
        return True, None
    if value == "false":
        return False, None
    return False, JSONResponse(status_code=422, content={
        "detail": f"{name} must be exactly \"true\" or \"false\" (or omitted, the default "
                  f"\"false\") -- strictly parsed, never coerced from another spelling; "
                  f"got {value!r}"})


_PAGE_TIE_RE = re.compile(r"^[0-9a-f]{32}$")


def _composite_cursor_tie_format_failure(name: str, value: str) -> JSONResponse | None:
    """Ledger rows 153/154 fix round (CRITICAL finding, coordinator fresh-context review of
    commit 6a104c0): `after_tie`'s own closed shape, checked BEFORE it ever crosses into a query
    -- the composite-keyset counterpart of `_query_string_representability_failure`/
    `_out_of_range_id` (ADR-0012 P1, same discipline, one param over). The legal domain is exact:
    the empty string (no tiebreaker supplied -- the default, walk-from-the-start-of-this-key-
    value posture) or exactly 32 lowercase hex characters (an md5 digest's own shape, the ONLY
    shape `_page_tie` -- this route's own per-row tiebreaker field -- ever takes). Anything else
    is a typed 422 naming the closed vocabulary; a malformed composite cursor is refused the SAME
    way every other malformed cursor on this route already is, never guessed at or silently
    truncated to fit. Returns the 422 `JSONResponse` on a violation, else `None`."""
    if value == "" or _PAGE_TIE_RE.fullmatch(value):
        return None
    return JSONResponse(status_code=422, content={
        "detail": f"{name} must be exactly 32 lowercase hex characters (an md5 digest's own "
                  f"shape -- the tiebreaker this route's own `_page_tie` response field carries) "
                  f"or omitted; got {value!r}"})


def _nonunique_tie_group_sql(schema: str, view: str, key_col: str, cursor_key_sql: str,
                              limit: int) -> str:
    """Round-2 fix (ledger rows 153/154, coordinator's second fresh-context re-review of
    6a104c0+15b2f78). The reviewer constructed the round-1 fix's own disclosed residual LIVE:
    two rows byte-identical in EVERY column (same `key_col` AND same `_page_tie`, since
    `_page_tie` is derived from the row's own full content) are genuinely indistinguishable --
    no per-row discriminator exists in the view's own output, and NONE can be manufactured
    stably. A THIRD cursor component (a `row_number() OVER (PARTITION BY key_col, _page_tie
    ORDER BY <a constant>)` ordinal, the reviewer's own first candidate to evaluate) was
    considered and REJECTED here: Postgres does not guarantee a stable row-to-ordinal
    assignment across SEPARATE query executions when the ORDER BY carries no real ordering
    key (only a same-execution guarantee) -- a byte-identical twin ARRIVING between two page
    requests (the ledger is append-only; nothing refuses a second identical write) can grow the
    group's membership between the query that computed page N's cursor and the query that
    computes page N+1, and the ordinal each physical row receives is then free to reshuffle: a
    row NOT YET served can be assigned an ordinal at or below the already-passed cursor
    position, which the `WHERE ordinal > cursor_ordinal` predicate then EXCLUDES FOREVER -- a
    silent, permanent drop, worked through by hand across every possible reshuffle in this
    fix's own commit message. The ordinal candidate is UNSOUND under the exact mid-walk-append
    case the coordinator asked to be reasoned through; it is not used.

    THE ACTUAL FIX needs no per-row discriminator at all: a byte-identical CONTENT GROUP
    (every row sharing this key_col value AND this exact `_page_tie`) is served ATOMICALLY --
    NEVER split across a page. `page` is the raw `LIMIT`-bounded fetch; `cutoff` is the last
    row `page` actually contains; the outer SELECT then serves every row in `filtered` up to
    AND INCLUDING the full `cutoff` group, not merely whatever fraction of it `LIMIT` happened
    to cut off mid-group -- so a page never ends inside a tie group, and there is no notion of
    "some group members served, some not" for an ordinal to ever have to break a tie within.
    This makes `limit` a SOFT floor for a non-unique-key view (a page MAY carry more rows than
    requested, by exactly the size of its own boundary group) -- disclosed here and in
    VIEW_REGISTRY's own comment, and bounded by `MAX_TIE_GROUP_EXTRA_ROWS` (`_tie_group_too_
    large`'s own docstring) against a pathologically large duplicate-content group.

    THE MID-WALK-APPEND CASE, worked through explicitly (this is what round-3 review will
    attack first, per the coordinator's own framing, so it is worked through here in full
    rather than asserted): a NEW byte-identical twin can only ever land in ONE of two temporal
    relationships to a client's in-flight walk, cut along the SAME (key_col, _page_tie) pair
    every page boundary is drawn on:
      (a) It arrives for a group the cursor has NOT YET REACHED (the client has not yet
          requested the page whose boundary would include that group). When that page IS
          requested, the query re-evaluates `filtered`/`page`/`cutoff` FRESH, sees the NOW-
          LARGER group, and serves the WHOLE group -- old member(s) and the new twin together,
          atomically, in that one page. No drop; the twin is served exactly once, alongside its
          siblings, on the FIRST request that reaches that group's boundary.
      (b) It arrives for a group the cursor has ALREADY PASSED (the client's own `after_tie`/
          `after_id`/`after_slug` cursor is already strictly greater than that group's own
          (key_col, _page_tie) pair). This twin is EXCLUDED from the remainder of THIS walk --
          but this is NOT a new hazard this fix introduces: it is the IDENTICAL, already-
          disclosed residual A11 already names for `/work/items`' own `after_slug` keyset ("a
          row inserted BEHIND an in-flight cursor is not visible to THAT walk -- no snapshot-
          free scheme over a non-append-monotonic key can promise otherwise -- it simply joins
          the NEXT walk"), extended here from "a row with a new key value" to "a row with a
          value tying an already-passed key". EVERY keyset-paginated route in this file --
          unique-key or not -- already carries this exact class of residual; this fix neither
          creates it nor makes it worse for the non-unique case.
    There is NO third case: a group's own (key_col, _page_tie) pair is a fixed coordinate on
    the SAME total order every page's WHERE/ORDER BY already walks, so "the cursor is mid-way
    through consuming this exact group, with some members served and some not" cannot occur --
    the atomic-extension design is exactly what forecloses that state from ever existing, which
    is why no per-row ordinal is needed to break a tie WITHIN it. The class is CLOSED for the
    append-before-reaching case (a), and the residual for the append-behind-cursor case (b) is
    the SAME pre-existing, already-disclosed one every other view already lives with -- not a
    new, silently-introduced gap.

    `cursor_key_sql` is a caller-validated SQL fragment (a checked-int literal for an id-shaped
    key, or a bound `:'after_slug'` placeholder for a slug-shaped key) -- never unvalidated
    caller text. `limit` is the ALREADY-validated `1 <= limit <= 1000` value; the group
    extension is deliberately NOT included in that same bound (see MAX_TIE_GROUP_EXTRA_ROWS'
    own docstring for the separate, wider bound that governs it instead)."""
    return (
        f"WITH candidate AS ("
        f"  SELECT v.*, md5(v::text) AS _page_tie FROM {schema}.{view} v"
        f"), filtered AS ("
        f"  SELECT * FROM candidate "
        f"  WHERE ({key_col}, _page_tie) > ({cursor_key_sql}, :'after_tie')"
        f"), page AS ("
        f"  SELECT * FROM filtered ORDER BY {key_col}, _page_tie LIMIT {limit}"
        f"), cutoff AS ("
        f"  SELECT {key_col} AS ck, _page_tie AS ct FROM page "
        f"  ORDER BY {key_col} DESC, _page_tie DESC LIMIT 1"
        f") "
        f"SELECT coalesce(jsonb_agg(t ORDER BY t.{key_col}, t._page_tie), '[]'::jsonb) "
        f"FROM filtered t, cutoff c "
        f"WHERE (t.{key_col}, t._page_tie) <= (c.ck, c.ct);"
    )


def _tie_group_too_large(view: str, extra: int) -> JSONResponse:
    """Round-2 fix (ledger rows 153/154): the loud refusal `views_view`'s non-unique-key branch
    returns instead of serving an unboundedly large page when the byte-identical content group
    at the page boundary has more members than `MAX_TIE_GROUP_EXTRA_ROWS` can atomically extend
    past. Typed, named disposition (the same shape `capability_absent`/`unknown_view` already
    establish). Round-3 fix (coordinator's third fresh-context re-review): status 409, not 500
    -- this file's own convention reserves 500 for `unclassified_failure` (a psql-level failure
    this boundary genuinely cannot classify further); this refusal is the OPPOSITE, a boundary-
    ENFORCED business rule the boundary understands completely and names precisely, the same
    shape every other typed 4xx refusal in this file already is. 409 (Conflict) is
    `boundary_cli_client.py`'s own `_READ_REFUSAL_STATUSES` set already recognizes as a read-side
    boundary refusal, so no client-side change was needed for this half of the fix."""
    return JSONResponse(status_code=409, content={
        "disposition": "tie_group_too_large",
        "view": view,
        "message": f"GET /views/{view}: the byte-identical row group at this page's own "
                   f"boundary has {extra} more member(s) than this boundary's own "
                   f"MAX_TIE_GROUP_EXTRA_ROWS={MAX_TIE_GROUP_EXTRA_ROWS} bound -- refused rather "
                   f"than served as one unboundedly large page (ADR-0002); this is a real, if "
                   f"unlikely, denial-of-service shape a keyset route must not absorb silently."})


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


def _log_infra_failure(route: str, method: str, exc: Exception) -> None:
    """The full, loud, un-redacted detail stays server-side (stderr -- this project's own house
    channel for a loud diagnostic every other construction-time refusal in this file already
    uses) -- never in the HTTP response (A2.4's exposure posture). The human stderr line's own
    combined "METHOD /path" text is UNCHANGED (spec: "their server-side-only discipline ... is
    unchanged") -- only the JSON event's FIELDS split `route`/`method` apart (fresh-context
    review finding (a), post-f450019: `route` must stay the bare path everywhere it appears,
    matching `request_start`/`request_end`, never method-prefixed on this event alone).

    Diagnostic-logging spec §2 L4: this is one of the THREE existing sites that migrate to a
    typed call site rather than staying a parallel stream -- the pre-existing human stderr line
    above is UNCHANGED; this JSON `infra_failure` event is added BESIDE it, not instead of it."""
    sys.stderr.write(f"boundary_service: INFRA FAILURE ({method} {route}): {exc}\n")
    boundary_diagnostic_log.log_event(
        boundary_diagnostic_log.Event.INFRA_FAILURE, route=route, method=method)


def _log_unclassified_failure(route: str, method: str, exc: Exception) -> None:
    """A4.3's sibling to `_log_infra_failure` -- the full detail (which, unlike an ordinary
    infra failure, may include the actual psql stderr naming the offending SQL/data) stays
    server-side only; the client sees `unclassified_failure`'s honest, cause-free message.
    Same `route`/`method` field split as `_log_infra_failure` above, same reason.

    Diagnostic-logging spec §2 L4: the second of the three migrated call sites -- the existing
    human stderr line below is unchanged; this JSON `unclassified_failure` event is added
    beside it."""
    sys.stderr.write(f"boundary_service: UNCLASSIFIED FAILURE ({method} {route}): {exc}\n")
    boundary_diagnostic_log.log_event(
        boundary_diagnostic_log.Event.UNCLASSIFIED_FAILURE, route=route, method=method)


class _BodyTooLarge(Exception):
    """Raised by `_read_bounded_body` (checkpoint a), via the `_bounded_raw_body`/
    `_bounded_artifact_body` FastAPI dependencies -- caught once, by the app-level exception
    handler (`create_app`), and turned into the typed `payload_too_large` response. Not caught
    inline in the write route itself (A3.1's plain-`def` shape) because the dependency runs
    BEFORE the (now synchronous, off-the-event-loop) handler is ever dispatched.

    `limit_bytes` (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part B) carries WHICH bound fired
    -- MAX_WRITE_BODY_BYTES for the four generic write routes, MAX_ARTIFACT_BODY_BYTES for
    `POST /artifacts` -- so the exception handler reports the bound that actually refused,
    never a hardcoded one (the SAME per-checkpoint honesty A8 already established between this
    checkpoint and MAX_PSQL_ARG_BYTES)."""

    def __init__(self, limit_bytes: int, observed_bytes: int, message: str) -> None:
        super().__init__(message)
        self.limit_bytes = limit_bytes
        self.observed_bytes = observed_bytes
        self.message = message


def _classify_parse_failure(exc: Exception) -> tuple[str, str]:
    """A3.2's parse closure: classify a body decode/parse failure by the axis it violates --
    encoding / value / structure -- WITHOUT ever echoing the raw body bytes back (the
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
        return "value", f"a numeric literal in the request body is too large to parse ({exc})"
    return "structure", f"the request body could not be parsed ({exc})"  # pragma: no cover


def _guard_recursion(callable_, *args, exceptions: tuple[type[BaseException], ...] = (RecursionError,), **kwargs):
    """THE single guarded-traversal helper (ledger row 1628 / work item
    boundary-recursion-net-single-invariant): every deep-walk call site in this module -- a
    call whose own recursion depth is driven by caller-supplied payload nesting, not this
    module's own bounded logic -- routes its `RecursionError` exposure through THIS ONE
    function, never an open-coded `except RecursionError` at the call site. Before this fix,
    A3.2 (`json.loads`), A13 (`json.dumps(..., allow_nan=False)`), and A7
    (`_representability_axis_failure`'s `_iter_strings` walk) each carried their OWN except
    clause -- three independently-authored nets sharing only the `_classify_parse_failure`
    classifier by convention, not by any structural guarantee a fourth traversal site added
    later would also route through it. `gates/deep_walk_recursion_guard.py` enforces the
    invariant mechanically: it refuses any `except ... RecursionError ...` clause anywhere in
    this file OUTSIDE this function's own body.

    Calls `callable_(*args, **kwargs)` and returns `(result, None, None)` on success. If it
    raises one of `exceptions` (default: `RecursionError` alone -- the recursion net's own
    scope; a caller may widen this to also fold in `ValueError`, e.g. the `json.loads` sites,
    where `_classify_parse_failure` already gives BOTH exception families the same typed-422
    treatment), returns `(None, axis, detail)` via `_classify_parse_failure`. Any OTHER
    exception propagates unchanged -- this helper's only job is the recursion net (and,
    optionally, whatever other exception types a caller explicitly opts into folding through
    the SAME classifier), never the full exception taxonomy each call site's OWN business
    logic still classifies for itself (e.g. `_reserialize_or_value_axis_failure`'s distinct
    "non-finite number" `ValueError` handling, which is NOT the same condition as a parse-time
    oversized-integer `ValueError` and keeps its own message)."""
    try:
        return callable_(*args, **kwargs), None, None
    except exceptions as e:
        axis, detail = _classify_parse_failure(e)
        return None, axis, detail


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

    A13 (post-fixpoint microamendment, ledger row 1621): this `json.dumps` call also routes its
    `RecursionError` exposure through `_guard_recursion` (row 1628's single-helper fix), the
    same typed structure-axis refusal A7 already gave the adjacent post-parse traversal
    (`_iter_strings`/`_representability_axis_failure`). Before A13, a deeply nested object
    reaching THIS call was protected only by the accident that `json.loads` overflows at the
    same-or-shallower depth on this CPython build -- not by any designed guarantee of this
    call's own. No caller input reaches this branch today (the loads-side guard fires first for
    every payload that ever parses); this replaces that accidental safety with a designed net,
    same message family as A7.

    Returns `(payload_json, None, None)` on success; on refusal, `(None, axis, detail)` naming
    WHICH axis failed -- `"value"` for a non-finite number (A4.1(a)) or A13's recursion net
    alike (row 1628 unified the axis vocabulary too -- see this module's own docstring), or
    `"structure"` if `_guard_recursion` ever reclassifies a `RecursionError` that way -- and
    the detail text, never echoing the payload back. The non-finite-number `ValueError` is
    NOT routed through `_guard_recursion` (it is a distinct condition from A3.2's parse-time
    oversized-integer `ValueError`, with its own message) -- only the `RecursionError` exposure
    is unified."""
    try:
        payload_json, axis, detail = _guard_recursion(json.dumps, payload, allow_nan=False)
    except ValueError as e:
        return None, "value", (
            f"the payload contains a non-finite number (Infinity/NaN, or a numeric "
            f"literal magnitude too large to represent as a finite float) that "
            f"JSON/jsonb cannot represent ({e})")
    if axis is not None:
        return None, axis, detail
    return payload_json, None, None


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


async def _read_bounded_body(request: Request, max_bytes: int = MAX_WRITE_BODY_BYTES) -> bytes:
    """A2.2 checkpoint (a): `max_bytes` enforced on the RAW request body, BEFORE any JSON
    parsing (default MAX_WRITE_BODY_BYTES, the four generic write routes' own bound; Part B's
    `POST /artifacts` calls this with MAX_ARTIFACT_BODY_BYTES instead -- see `_bounded_artifact_
    body`). Two sub-cases, both named in the spec: a Content-Length header, when the client sent
    one, is checked FIRST and refuses without ever reading the body (the 100 MB whole-body-
    buffered-then-parsed hazard A2.2 names, foreclosed before a single byte is read); a body with
    no (or a lying) Content-Length is bounded by reading it incrementally and aborting the
    instant the running total exceeds the bound -- never buffered whole first and measured
    after."""
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared = int(content_length)
        except ValueError:
            declared = None
        if declared is not None and declared > max_bytes:
            raise _BodyTooLarge(
                max_bytes, declared,
                f"the request's Content-Length ({declared} bytes) exceeds the "
                f"{max_bytes}-byte write bound (checkpoint a, before JSON parsing) "
                f"-- refused before reading the body.")
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > max_bytes:
            raise _BodyTooLarge(
                max_bytes, total,
                f"the request body exceeds the {max_bytes}-byte write bound "
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


async def _bounded_artifact_body(request: Request) -> bytes:
    """design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part B's sibling to `_bounded_raw_body` above,
    for `POST /d/{deployment}/artifacts` alone -- the SAME body-read-timeout wrapping, bounded by
    MAX_ARTIFACT_BODY_BYTES instead of MAX_WRITE_BODY_BYTES (an artifact payload's base64 `bytes`
    field can legitimately approach ~1.4 MiB for a kernel-cap-sized upload, well past the four
    generic write routes' own 1 MiB bound -- see MAX_ARTIFACT_BODY_BYTES's own docstring for why
    this is not a second size judgment)."""
    try:
        return await asyncio.wait_for(
            _read_bounded_body(request, MAX_ARTIFACT_BODY_BYTES), timeout=BODY_READ_TIMEOUT_S)
    except asyncio.TimeoutError as e:
        raise _BodyReadTimeout(
            BODY_READ_TIMEOUT_S,
            f"the request body was not fully received within BODY_READ_TIMEOUT_S="
            f"{BODY_READ_TIMEOUT_S}s (a stalled/trickled body-read phase, distinct from the "
            f"psql-phase time axis, spec A5.3) -- refused."
        ) from e


# ================================================================================================
# SSE PUSH SIGNAL (design/FABLE-BOUNDARY-SSE-EVENTS-SPEC.md, maintainer pre-ratified, work item
# boundary-sse-events, ledger row 169). `GET /d/{deployment}/events` -- a HEAD-ADVANCEMENT-ONLY
# signal (spec §1: "when a deployment's ledger head grows, subscribers receive one event `event:
# head` with data `{"head_id": <n>}`. No row content ever crosses the stream"). See the spec's
# own §1-§4 for the full mechanics; this section and the `/events` route below (inside
# `create_app`) implement them.
# ================================================================================================

SSE_KEEPALIVE_INTERVAL_S = 15.0
"""Spec §1 item 3: a `: keepalive` comment line, emitted at least this often on every open SSE
stream, so an intermediary proxy does not reap an idle connection. NOT config-overridable (the
spec names only the poll interval and the client cap, below, as operator tunables) -- this is a
protocol-hygiene constant every stream needs identically, not an operational bound an operator
would ever have reason to widen."""

_SSE_SHUTDOWN_SENTINEL = object()
"""Ledger row 554 (work item hub-shutdown-drain-hang): a distinct singleton, never a real head
id (real head ids are positive kernel row ids -- `ledger.id`'s own domain), pushed onto every
ALREADY-REGISTERED live subscriber queue by `_BoundaryUvicornServer.shutdown` (below) as soon as
this process begins shutting down. `_stream()`'s own read loop (inside `create_app`) checks for
this object identity and breaks immediately on it -- the same code path an ordinary
head-advancement event takes, minus the `yield`. ROOT CAUSE this closes (reproduced on a scratch
hub, `env -u PGOPTIONS`, real SIGTERM, py-spy unavailable in this sandbox so witnessed via an
in-process `asyncio.all_tasks()` debug probe instead, plus a committed red-first regression leg,
seen-red/boundary-sse-events/run_fixtures.py's own S12): spec §1 item 5 states plainly that a
restart's SIGTERM should simply kill every open SSE connection ("connections die at restart ON
PURPOSE -- nothing needs graceful SSE draining"), but the STOCK uvicorn 0.51 shutdown path does
not actually do that for a connection whose ASGI response is still in progress --
`uvicorn.protocols.http.httptools_impl.HttpToolsProtocol.shutdown` only closes the transport
`if self.cycle is None or self.cycle.response_complete`; for a still-streaming SSE response
(never `response_complete` by construction -- it only ends when THIS generator returns) it
takes the OTHER branch, `self.cycle.keep_alive = False`, and leaves the connection running.
`uvicorn.server.Server.shutdown` then awaits `_wait_tasks_to_complete()` (which loops on
`server_state.connections`/`server_state.tasks` being empty) wrapped in `asyncio.wait_for(...,
timeout=self.config.timeout_graceful_shutdown)` -- and this codebase's own `uvicorn.Config(...)`
construction (`main()`, below) never set `timeout_graceful_shutdown`, so it defaulted to `None`,
i.e. NO timeout at all. `_wait_tasks_to_complete` only escapes early via `self.force_exit`,
which uvicorn's own `handle_exit` sets ONLY on a SECOND `SIGINT` -- never on plain `SIGTERM`,
and `libexec/autoharn-service`'s `restart` verb (the one the live incident actually used) only
ever sends `SIGTERM`, then (only if the operator explicitly passes `--force-kill` after its own
bounded refusal) `SIGKILL` -- never a second `SIGINT` through uvicorn's own signal machinery, so
this raw hang was never self-healing on `restart`'s own path (`stop`'s separate 5s-then-auto-
SIGKILL posture is a different verb with a different, already-bounded contract -- not what this
fix is about). Net effect: one live SSE connection open at SIGTERM time blocked the drained
restart INDEFINITELY -- witnessed live: a scratch hub with a still-open `curl -N .../events`
connection did not exit even after 120s of waiting past SIGTERM (vs. ~0.2s for a genuinely idle
hub, with or without a PRIOR, already-disconnected SSE probe -- that half of the incident
report's own suspect list, the watcher/keepalive LOOP, was cleared: both `hub.connect`'s
lazy-start and `hub.disconnect`'s empty-subscribers stop already ran correctly and left no
lingering watcher task in every variant tried). This sentinel fix wakes every subscriber PARKED
ON ITS QUEUE -- every `_stream()` generator blocked in a `queue.get`-shaped read waiting for the
next event -- matching spec §1 item 5's own stated intent for that case, rather than depending on
uvicorn's generic (and here, unbounded) connection-close machinery at all. This is narrower than
"every already-connected stream": a subscriber whose request task is instead blocked further down
the stack inside uvicorn's own `flow.drain()` (a stalled or slow reader on the other end of the
TCP connection, or a closed TCP receive window, backing up the ASGI `send()` this generator's own
`yield` is suspended in) is NOT parked on the queue and so never observes this `put_nowait` --
`queue.put_nowait` reaches a task waiting to receive FROM the queue; it cannot reach one already
past that point and stuck writing TO the socket. A backpressure-blocked writer is instead bounded
by `_UVICORN_GRACEFUL_SHUTDOWN_TIMEOUT_S`'s finite backstop -- an honest residue, alongside the
separately-disclosed pre-registration-race residue below. (Waking a `flow.drain`-blocked task
cleanly is not pursued here: the case is already bounded by the backstop, and the plumbing to
reach into uvicorn's own flow-control internals is not worth the complexity for a bounded gap.)

RESIDUAL, DISCLOSED (fresh-context review finding): a connection whose handler is suspended
inside `_SseHub.connect()`'s own one `await` (the immediate catch-up poll, BEFORE `queue` is
added to `hub.subscribers`) at the exact instant the broadcast below runs is NOT yet a
subscriber and so does not receive this sentinel -- it falls through to the finite
`_UVICORN_GRACEFUL_SHUTDOWN_TIMEOUT_S` backstop instead of the fast path. This window is narrow
(bounded by `main_loop`'s own 0.1s `should_exit` poll cadence plus one `_sse_query_head` poll,
ordinarily milliseconds) and its worst case is now bounded (the backstop), never unbounded (the
pre-fix defect) -- narrowing it further was not pursued here since doing so would cost either
unconditional extra shutdown latency on the always-idle common path (this ticket's own `under a
second` requirement) or a second broadcast pass gated on evidence of live traffic, and the
residual is already a bounded-not-infinite gap, not the ticket's defect class. See
`_BoundaryUvicornServer.shutdown`'s own docstring for the other half (the defensive, finite
backstop bound) and `PSQL_EXEC_TIMEOUT_S`, above, for why that backstop's value is what it is."""

# The two SSE tunables (spec §1 items 1/4), DEFAULT-set from boundary_multiplex_config's own
# defaults, overridden once at startup (`main()`) via the `configure_*` functions below --
# construction-time-defense-in-depth, the SAME pattern `configure_identity_enforcement`/
# `boundary_diagnostic_log.configure_level` already establish: the TOML value is already
# validated whole-file by boundary_multiplex_config.py before either function here ever runs.
_sse_poll_interval_secs: float = boundary_multiplex_config.DEFAULT_SSE_POLL_INTERVAL_SECS
_max_sse_clients: int = boundary_multiplex_config.DEFAULT_MAX_SSE_CLIENTS


def configure_sse_poll_interval(v: float) -> None:
    global _sse_poll_interval_secs
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
        raise ValueError(
            f"boundary_service: REFUSED -- configure_sse_poll_interval({v!r}) must be a "
            f"positive number.")
    _sse_poll_interval_secs = float(v)


def configure_max_sse_clients(v: int) -> None:
    global _max_sse_clients
    if isinstance(v, bool) or not isinstance(v, int) or v < 1:
        raise ValueError(
            f"boundary_service: REFUSED -- configure_max_sse_clients({v!r}) must be a positive "
            f"integer.")
    _max_sse_clients = v


def _sse_query_head(cfg: "BoundaryConfig") -> int:
    """The ONE query the shared watcher (and a connecting subscriber's own immediate catch-up
    check) runs: this deployment's ledger head (`max(id)`, 0 on an empty ledger -- `coalesce`
    matches every other read route's own empty-result convention in this file). Runs through
    `_psql`/`_query_json` exactly like every other kernel read here -- the SAME admission gates
    (global + per-deployment) apply to this call, so a saturated deployment simply skips a poll
    cycle (caught by the caller) rather than being exempted from the bound the rest of this
    service already lives under."""
    return int(_query_json(cfg, f"SELECT to_jsonb(coalesce(max(id), 0)) FROM {cfg.schema}.ledger;"))


# The exceptions `_sse_query_head` can surface through `_psql`/`_query_json` -- every caller of
# `_sse_query_head` catches exactly this tuple (ADR-0012 P1: named once, not re-derived per call
# site) and treats each as "this poll attempt did not succeed", never a stream-ending failure --
# the watcher/connect path simply tries again next cycle (`KernelCallSaturated`/
# `DeploymentCallSaturated`: ordinary load, expected to clear; `PsqlInfraFailure`/
# `PsqlUnclassifiedFailure`: the SAME transient-infra postures every other read route in this
# service already answers with a typed refusal for, here absorbed rather than surfaced because an
# SSE watcher has no single request to answer -- it just tries again). Named AFTER the four
# classes themselves (this section sits below `PsqlInfraFailure`/`KernelCallSaturated`/
# `DeploymentCallSaturated`/`BoundaryConfig`/`_psql`/`_query_json` in this file precisely so this
# tuple can reference the real classes rather than string-matching class names).
_SSE_POLL_EXCEPTIONS = (
    KernelCallSaturated, DeploymentCallSaturated, PsqlInfraFailure, PsqlUnclassifiedFailure,
)


class _SseHub:
    """One instance PER DEPLOYMENT (built once, in `create_app`, alongside that deployment's own
    `BoundaryConfig` -- never re-derived per request). Owns the lazy-start/stop watcher task and
    the live subscriber set for that deployment's `/events` route.

    LIFECYCLE (spec §1 item 1, "one shared watcher per deployment, started lazily on first
    subscriber, stopped when the last unsubscribes"): `connect()` runs its one head-poll `await`
    FIRST, then adds the caller's queue to `subscribers` and starts `_watch_loop` as an asyncio
    task IFF one is not already running, with no `await` between those two steps (row-429/
    sse-subscriber-slot-leak: this ordering makes registration and cancellation-safety
    inseparable -- a cancellation during the poll never registers the queue at all, so there is
    nothing for `disconnect()` to clean up); `disconnect()` removes the queue (a no-op if it was
    never added) and, if `subscribers` is now empty, cancels the watcher task and clears the
    reference -- so a deployment with zero live subscribers holds no running task at all
    (witnessed via `app.state.sse_hubs`, see seen-red/boundary-sse-events/run_fixtures.py's own
    in-process leak witness, and seen-red/boundary-sse-events/run_fixtures.py's cancellation-
    during-connect leak witness added for this fix). `self.lock` (an `asyncio.Lock`, this hub is
    only ever touched from the single uvicorn event loop thread, matching every other
    asyncio-native piece of this service) serializes the subscribe/unsubscribe/start/stop
    transitions against each other and against the watcher's own tail check, so two
    near-simultaneous connects never start two watcher tasks and a connect racing a would-be-final
    disconnect never leaves a watcher running with zero subscribers or a hole with subscribers and
    no watcher."""

    def __init__(self, cfg: "BoundaryConfig") -> None:
        self.cfg = cfg
        self.subscribers: set[asyncio.Queue] = set()
        self.watcher_task: asyncio.Task | None = None
        self.last_head: int = 0
        self.lock = asyncio.Lock()

    async def connect(self, queue: "asyncio.Queue[int]") -> int:
        """Runs ONE immediate, synchronous poll (spec §1 item 2: "on connect the server
        immediately emits the current head if it exceeds [the caller's Last-Event-ID]") --
        this cannot simply trust `self.last_head` as already fresh, because the watcher task
        may not have observed a very recent write yet -- BEFORE registering `queue` as a live
        subscriber or starting the watcher (row-429/work-item sse-subscriber-slot-leak: this
        ordering is deliberate and load-bearing, not cosmetic). The poll is the only `await` in
        this method, hence the only point a caller's cancellation/timeout can land on; running
        it before registration means a cancellation here simply never registers the queue --
        nothing to leak, no `finally`/`disconnect()` required to make this call itself safe.
        Once the poll (or its typed-absorb fallback) has a `head` value, the actual
        registration + lazy watcher-start happen inside `self.lock` with NO further `await`
        between acquiring the lock and releasing it (`asyncio.Queue.add`/`asyncio.create_task`
        are synchronous calls), so once this method starts touching `self.subscribers` it always
        finishes untouched by cancellation -- either the queue is fully registered and the
        watcher invariant holds, or the queue was never added at all. A transient poll failure
        degrades to the last KNOWN head rather than failing the connection -- `/events` never
        surfaces a `_psql`-layer failure as anything other than "no new information yet"; a
        genuinely down kernel is still visible via every OTHER route's own typed
        `infra_failure`. Returns the (possibly just-updated) head this deployment is known to
        be at."""
        try:
            head = await asyncio.to_thread(_sse_query_head, self.cfg)
        except _SSE_POLL_EXCEPTIONS:
            head = self.last_head
        async with self.lock:
            if head > self.last_head:
                self.last_head = head
            self.subscribers.add(queue)
            if self.watcher_task is None or self.watcher_task.done():
                self.watcher_task = asyncio.create_task(self._watch_loop())
            return self.last_head

    async def disconnect(self, queue: "asyncio.Queue[int]") -> None:
        """Spec §1 item 1's other half: stops the watcher the instant the LAST subscriber
        leaves (never lingering, never leaking a task with nothing to serve). Idempotent and
        safe to call with a `queue` that was NEVER registered (e.g. `connect()` above never
        reached the registration step for it) -- `set.discard` is a no-op on a missing member,
        and the emptiness check below reflects whatever `self.subscribers` actually holds, so
        calling this defensively from `_stream()`'s own `finally` (belt-and-suspenders on top of
        `connect()`'s own cancellation-safety above) can never mis-cancel a watcher some OTHER
        still-registered subscriber still needs."""
        async with self.lock:
            self.subscribers.discard(queue)
            if not self.subscribers and self.watcher_task is not None:
                self.watcher_task.cancel()
                self.watcher_task = None

    async def _watch_loop(self) -> None:
        """The ONE shared poller for this deployment (spec §1 item 1) -- sleeps
        `_sse_poll_interval_secs`, polls once, and (on a genuine head advance) pushes the new
        head onto every live subscriber's own queue; a transient poll failure (see
        `_SSE_POLL_EXCEPTIONS` above) is silently absorbed and retried next cycle, never raised
        past this loop (there is no single request here to answer with a typed refusal). Runs
        until `disconnect()` cancels it (the last-unsubscribe stop) -- `asyncio.CancelledError`
        is the ordinary, expected exit, not an error."""
        try:
            while True:
                await asyncio.sleep(_sse_poll_interval_secs)
                try:
                    head = await asyncio.to_thread(_sse_query_head, self.cfg)
                except _SSE_POLL_EXCEPTIONS:
                    continue
                if head > self.last_head:
                    async with self.lock:
                        self.last_head = head
                        subs = list(self.subscribers)
                    for q in subs:
                        q.put_nowait(head)
        except asyncio.CancelledError:
            pass


_UVICORN_GRACEFUL_SHUTDOWN_TIMEOUT_S = PSQL_EXEC_TIMEOUT_S + 5.0
"""Row 554 (hub-shutdown-drain-hang) defensive backstop -- see `_BoundaryUvicornServer.shutdown`'s
own docstring for the PRIMARY fix (an immediate SSE-stream wake, not a wait). This is belt-and-
suspenders on top of that: stock `uvicorn.Config(...)` defaults `timeout_graceful_shutdown` to
`None`, i.e. NO bound at all, on the internal `asyncio.wait_for(self._wait_tasks_to_complete(),
timeout=...)` uvicorn's own `Server.shutdown` runs -- meaning ANY future long-lived connection
class this service ever grows (not just SSE, and not just a case this file's own code can
foresee) would reproduce the exact same indefinite-hang hazard the SSE stream did, with no floor
under it at all. Bounding it here, finite, means the WORST case at THIS layer is now "uvicorn
force-cancels remaining tasks after this many seconds", never "forever, only `--force-kill` gets
you out" -- but this layer is the SECOND of two, not the operator's actual bound; read both
before trusting the number:

THE LAYERED TIMEOUT STORY, honestly stated:

(a) THE OPERATOR BOUND, and the one that actually fires first in practice: `libexec/
autoharn-service`'s `restart` verb (`_DEFAULT_DRAIN_TIMEOUT_S = 30.0`, `--drain-timeout`
overridable, no upper bound) polls the OS pid for exit and, on timeout, refuses to escalate
unasked -- only an explicit `--force-kill` re-run sends `SIGKILL`. This is the normal path: an
operator waiting past their own drain window chooses, explicitly, to either wait longer or force
the issue. This in-process constant is NOT that bound and does not replace it -- it fires INSIDE
the child process, on a completely separate clock, and by construction (`+ 5.0` margin) is sized
to still be running when `restart`'s own default 30s window closes, so the OPERATOR's own refusal
is what an operator watching a stuck restart actually sees first, not this backstop.

(b) THIS BACKSTOP is last-resort, reached only if an operator's own verb window has ALREADY
closed and they chose to keep waiting anyway (or set `--drain-timeout` past `PSQL_EXEC_TIMEOUT_S
+ 5.0`) rather than force-kill. It is not a true worst-case bound under saturation: `_psql`'s own
`_KERNEL_CALL_SEMAPHORE` (`MAX_INFLIGHT_KERNEL_CALLS = 24`) gates kernel calls, but a plain-`def`
handler is dispatched to Starlette's shared ASGI threadpool BEFORE it ever reaches that gate --
and anyio's `to_thread.run_sync` queues on its own `CapacityLimiter` (default 40 tokens) at THAT
point, ahead of and independent of the 24-slot kernel-call admission bound this file otherwise
relies on. A request queued in the threadpool dispatch when this backstop fires has not yet
started its own `PSQL_EXEC_TIMEOUT_S`-bounded work at all; this constant's derivation assumes the
task is already running its bounded psql phase, which is not guaranteed under threadpool
saturation. The accepted trade, stated plainly: this backstop can force-cancel a queued-but-
legitimate request in that saturated case, and that is judged acceptable against the alternative
it replaces -- the witnessed, reproduced-live, genuinely UNBOUNDED hang (row 554) that existed
before this fix, which had no floor at all. A finite bound with a disclosed, narrow overclaim
residue is still strictly better than no bound.

Sized at `PSQL_EXEC_TIMEOUT_S` (the longest a single, genuinely-slow ordinary request's own psql
call is ever allowed to run, once it IS running) plus a small margin -- long enough that a real
in-flight write still gets its full drain in the common (non-saturated) case, short enough to be
a meaningfully finite floor rather than a
nominal one that never actually bites in practice."""


class _BoundaryUvicornServer(uvicorn.Server):
    """Row 554 (work item hub-shutdown-drain-hang): the ONE override this subclass makes --
    `shutdown()`, below -- is the PRIMARY fix for a real, witnessed drain hang (see
    `_SSE_SHUTDOWN_SENTINEL`'s own docstring for the full root-cause trace). `main()` constructs
    THIS class instead of a bare `uvicorn.Server`/`uvicorn.run()` on both its own code paths
    (the `--pidfile` branch and the plain one) -- same `uvicorn.Config`, same `.run(...)` call
    shape, nothing else about startup/serving changes; this is a narrow override, not a
    reimplementation."""

    async def shutdown(self, sockets: list[socket.socket] | None = None) -> None:
        """Runs BEFORE `uvicorn.Server.shutdown`'s own (unmodified, via `super()`) connection-
        drain wait -- design/FABLE-BOUNDARY-SSE-EVENTS-SPEC.md §1 item 5 states plainly that a
        restart's SIGTERM should simply end every open SSE connection ("connections die at
        restart ON PURPOSE -- nothing needs graceful SSE draining"), but stock uvicorn 0.51 does
        NOT actually do that for a connection whose ASGI response is still streaming (see
        `_SSE_SHUTDOWN_SENTINEL`'s docstring for the exact mechanism witnessed: `httptools_impl.
        HttpToolsProtocol.shutdown` only closes the transport once `response_complete`, which an
        open SSE stream never is until ITS OWN generator returns) -- so without this override, a
        single live SSE connection at SIGTERM time blocked the ENTIRE drained restart
        indefinitely (witnessed: >120s, no exit, on a scratch hub with one open `curl -N`
        subscriber and zero ordinary inflight requests; the same scratch hub drained in ~0.2s
        both fully idle and after a PRIOR, already-disconnected SSE probe -- so the leaked-
        watcher-task branch of the original suspect list was cleared, not the actual cause).

        Fix: broadcast `_SSE_SHUTDOWN_SENTINEL` to every live subscriber queue on every
        deployment's `_SseHub`, right here, before ever awaiting uvicorn's own generic task-wait
        -- each open `_stream()` generator (inside `create_app`) wakes on its very next queue
        read (bounded by that read's own `SSE_KEEPALIVE_INTERVAL_S`-second `wait_for`, already
        in progress or about to start) and exits its loop immediately, exactly as if the client
        itself had disconnected. Ordinary (non-SSE) in-flight requests are never registered on
        any `_SseHub` and are completely untouched by this loop -- `super().shutdown(...)`,
        called immediately after, still drains them exactly as stock uvicorn always has.
        `getattr(..., "sse_hubs", {})` (never a bare `.sse_hubs`) is deliberate: `create_app`
        is the ONLY place that ever sets this attribute, and every real caller of THIS class
        does route through it, but a future test harness constructing a bare `FastAPI()` by
        hand for some other purpose should degrade to "nothing to broadcast to", never an
        `AttributeError` crash mid-shutdown.

        Wakes every subscriber PARKED ON ITS QUEUE (every ALREADY-REGISTERED subscriber whose
        `_stream()` generator is blocked in the queue read this `put_nowait` targets) -- see
        `_SSE_SHUTDOWN_SENTINEL`'s own docstring for the two connection states this broadcast
        cannot reach, both disclosed there: a subscriber whose request task is instead blocked in
        uvicorn's own `flow.drain()` (a stalled/slow reader, backpressure-blocked writer) never
        observes this `put_nowait` and is bounded by the backstop instead; and a handler still
        inside `_SseHub.connect()`'s own pre-registration poll at this exact instant ("RESIDUAL,
        DISCLOSED" there) is not yet a subscriber at all. `_UVICORN_GRACEFUL_SHUTDOWN_TIMEOUT_S`
        below is the deliberate backstop for both narrow, bounded gaps rather than a second
        broadcast pass here."""
        sse_hubs: dict[str, "_SseHub"] = getattr(self.config.app.state, "sse_hubs", {})
        for hub in sse_hubs.values():
            for queue in list(hub.subscribers):
                queue.put_nowait(_SSE_SHUTDOWN_SENTINEL)
        await super().shutdown(sockets=sockets)


def sse_saturated(max_clients: int, message: str) -> JSONResponse:
    """Spec §1 item 4: the one typed shape `GET /d/{deployment}/events` returns when
    `max_sse_clients` concurrent SSE connections are already open on this hub -- HTTP 503,
    naming the bound, distinct from `server_saturated`/`deployment_saturated` (this axis is never
    the 24-slot inflight admission gate -- an SSE connection never occupies that gate at all)."""
    body = SseSaturated(max_clients=max_clients, message=message)
    boundary_diagnostic_log.log_event(boundary_diagnostic_log.Event.REFUSAL, disposition=body.disposition)
    return JSONResponse(status_code=503, content=body.model_dump())


def create_app(configs: dict[str, BoundaryConfig]) -> FastAPI:
    """Multiplex spec §2: ONE app serves every deployment in `configs`, discriminated by the
    leading `/d/{deployment}` path segment on every route -- no unprefixed routes survive (the
    route table stays closed and single-shaped, not dual-dialect; a single-deployment config is
    the degenerate, expected common case, and the discriminator is still mandatory for it,
    spec §2). Each handler below resolves its own `{deployment}` segment via
    `_resolve_deployment` FIRST, returning the typed 404 `unknown_deployment` immediately when
    it is not a key of `configs` -- everything past that point is byte-identical to the
    single-deployment predecessor's own handler body (the resolved `cfg` local shadows the
    parameter name every pre-multiplex query below already used, so no query text changes)."""
    app = FastAPI(
        title="autoharn ledger boundary service",
        description="The outer declared Port into an autoharn-managed ledger "
                     "(design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md; design/"
                     "FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md). Reads serve kernel "
                     "views verbatim; writes pass through the s43 boundary functions and "
                     "return the kernel's own write_verdict verbatim. Every route is "
                     "discriminated by a leading /d/{deployment} segment (multiplex spec §2).",
        # A2.1: no self-documentation surface, disabled not merely unenumerated -- see this
        # module's docstring, "NO META-ROUTES". §9's route table is EXACTLY §3+§4's endpoints.
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    # design/FABLE-BOUNDARY-SSE-EVENTS-SPEC.md §1 item 1: one `_SseHub` PER DEPLOYMENT, built
    # once here (never re-derived per request) -- a plain closure variable, the SAME shape
    # `configs` itself already is, rather than a module-level global (which would collide across
    # the multiple `create_app` calls this file's own fixture bank already makes in one process,
    # e.g. W12's in-process route-table assertion). Also stashed on `app.state` -- Starlette's
    # own place for exactly this kind of app-scoped bookkeeping -- so an in-process witness (no
    # live HTTP needed) can drive `hub.connect`/`hub.disconnect` directly and observe
    # `hub.watcher_task` transition to `None` after the last unsubscribe (seen-red/
    # boundary-sse-events/run_fixtures.py's own leak witness).
    sse_hubs: dict[str, _SseHub] = {name: _SseHub(cfg) for name, cfg in configs.items()}
    app.state.sse_hubs = sse_hubs

    @app.middleware("http")
    async def _diagnostic_logging_middleware(request: Request, call_next):
        # Diagnostic-logging spec §2 L1, emission site (a): ASYNC middleware, per the row-1498
        # witness (see boundary_diagnostic_log's own module docstring, "THE WITNESSED
        # CONSTRAINT") -- never a plain-`def` dependency, whose own ContextVar.set() from
        # inside the threadpool would be silently lost on write-back. This middleware runs on
        # the event loop, ahead of routing/exception-handling (both of which run INSIDE
        # `call_next` here); every plain-`def` route handler below is dispatched to the
        # threadpool with a COPY of the context this middleware set, so it reads (and, via
        # `bind_deployment`, mutates an attribute of) the SAME RequestContext object.
        request_id = secrets.token_hex(8)
        ctx = boundary_diagnostic_log.RequestContext(
            request_id=request_id,
            route=request.url.path,
            method=request.method,
            client_addr=request.client.host if request.client is not None else None,
        )
        token = boundary_diagnostic_log.REQUEST_CONTEXT.set(ctx)
        started = time.monotonic()
        boundary_diagnostic_log.log_event(
            boundary_diagnostic_log.Event.REQUEST_START, route=ctx.route, method=ctx.method)
        response: Response | None = None
        try:
            # design/FABLE-DISPATCH-MECHANICS-SPEC.md §1/§2: identity parsing runs HERE, on
            # every request, before `call_next` -- so a bounded/malformed-header refusal never
            # reaches routing, and a resolved identity is on `REQUEST_CONTEXT` for every
            # downstream route handler AND every `_psql` call this request makes. Oversized or
            # malformed -> typed IdentityHeaderInvalid, BEFORE any kernel call (`call_next` is
            # never invoked on this path).
            try:
                resolution_case, principal_id, vendor_stamp = _parse_identity_headers(request.headers)
            except _IdentityRefusal as e:
                body = IdentityHeaderInvalid(header=e.header, message=e.message)
                boundary_diagnostic_log.log_event(
                    boundary_diagnostic_log.Event.REFUSAL, disposition=body.disposition,
                    header=e.header)
                response = JSONResponse(status_code=422, content=body.model_dump())
                return response
            boundary_diagnostic_log.bind_identity(
                resolution_case, principal=principal_id, vendor_stamp=vendor_stamp)
            # rung (a) (spec §3, ledger row 1471 sub-item 4c): an ANONYMOUS authority-bearing
            # write refuses once this deployment's identity_enforcement posture is "enforce" --
            # "grace" (the default) accepts it unchanged, byte-identical, so the operator
            # surface is never broken mid-migration. Checked here, not per-route (ADR-0012 P1:
            # one gate, every /write/*+/artifacts route inherits it) -- deliberately BEFORE
            # deployment resolution, since the posture is process-global (mirrors log_level's
            # own scope), not per-deployment.
            if (resolution_case == "anonymous"
                    and _identity_enforcement_posture == "enforce"
                    and _is_authority_bearing_write(request.method, request.url.path)):
                body = AnonymousWriteRefused(
                    message="this write carries neither a vendor stamp nor a minted-principal "
                            "identity header, and this deployment's identity_enforcement "
                            "posture is 'enforce' (design/FABLE-DISPATCH-MECHANICS-SPEC.md §3, "
                            "ledger row 1471 sub-item 4c: 'anonymous sessions keep NO write "
                            "surface beyond journaled refusals'). Nothing was written.")
                boundary_diagnostic_log.log_event(
                    boundary_diagnostic_log.Event.REFUSAL, disposition=body.disposition)
                response = JSONResponse(status_code=403, content=body.model_dump())
                return response
            response = await call_next(request)
            return response
        finally:
            duration_ms = (time.monotonic() - started) * 1000
            # Every operational failure this service raises (PsqlInfraFailure, saturation, a
            # write refusal, ...) is caught by one of this app's OWN registered exception
            # handlers, which run INSIDE `call_next` (Starlette's exception-handling machinery
            # sits below this user middleware, above routing) -- so `response` is populated
            # with the typed status code on every path this service's own code can reach.
            # `-1` below is reserved for a TRULY unhandled exception (a genuine bug this
            # service's own typed shapes do not cover) escaping past this point entirely --
            # Starlette's outer ServerErrorMiddleware still turns that into a bare 500 for the
            # client; this sentinel just distinguishes that path from an already-typed one in
            # the log, honestly, rather than fabricating a status this middleware never saw.
            status = response.status_code if response is not None else -1
            boundary_diagnostic_log.log_event(
                boundary_diagnostic_log.Event.REQUEST_END,
                route=ctx.route, status=status, duration_ms=duration_ms)
            boundary_diagnostic_log.REQUEST_CONTEXT.reset(token)

    @app.exception_handler(PsqlInfraFailure)
    async def _infra_failure_handler(request: Request, exc: PsqlInfraFailure) -> JSONResponse:
        # A2.4, narrowed per A3.2, narrowed FURTHER per A4.3: the ONE place a genuinely
        # connection-level psql failure (exit 2 -- unreachable world, connection refusal -- or a
        # PSQL_EXEC_TIMEOUT_S stall -- the ONLY things that raise PsqlInfraFailure as of A4.3)
        # becomes a typed 503, for every route uniformly (ADR-0012 P1: one handler, not a
        # try/except duplicated per route). Registered on the DEDICATED exception class, never
        # the bare `RuntimeError` a foreign failure (RecursionError, for one) could also raise.
        _log_infra_failure(request.url.path, request.method, exc)
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
        _log_unclassified_failure(request.url.path, request.method, exc)
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

    @app.exception_handler(DeploymentCallSaturated)
    async def _deployment_call_saturated_handler(request: Request, exc: DeploymentCallSaturated) -> JSONResponse:
        # Multiplex spec §4: the ONE place a DEPLOYMENT's own sub-bound saturation becomes a
        # typed 503, distinct from the global server_saturated handler above -- deliberately NOT
        # logged server-side, same rationale as KernelCallSaturated (ordinary, expected,
        # caller-actionable load, not a server-side anomaly).
        deployment = request.path_params.get("deployment", "?")
        cfg = configs.get(deployment)
        limit = cfg.dep_limit if cfg is not None else compute_per_deployment_limit(len(configs))
        return deployment_saturated(deployment, limit, str(exc))

    @app.exception_handler(_BodyTooLarge)
    async def _body_too_large_handler(request: Request, exc: _BodyTooLarge) -> JSONResponse:
        # A2.2 checkpoint (a), re-homed here now that body-reading is a DEPENDENCY (async, so
        # it can await the ASGI body stream) rather than inline in the (now plain `def`, A3.1)
        # write handler -- a dependency's exception propagates to the app's own exception
        # handling before the handler is ever dispatched to the threadpool, so this is still
        # the ONE place checkpoint (a) becomes the typed 413 (ADR-0012 P1). A8: checkpoint
        # (a)'s bound is the raw-body/buffering one, and limit_bytes says so honestly -- carried
        # on the exception itself (Part B: two DIFFERENT checkpoint-(a) bounds now exist,
        # MAX_WRITE_BODY_BYTES and MAX_ARTIFACT_BODY_BYTES; never hardcode one here again).
        return payload_too_large(exc.limit_bytes, exc.observed_bytes, exc.message)

    @app.exception_handler(_BodyReadTimeout)
    async def _body_read_timeout_handler(request: Request, exc: _BodyReadTimeout) -> JSONResponse:
        # A5.3: the body-read phase's own time bound, symmetric with the body_too_large handler
        # directly above -- a dependency's exception propagates to the app's own exception
        # handling before the (now synchronous, off-the-event-loop) handler is ever dispatched.
        body = BodyReadTimeout(timeout_s=exc.timeout_s, message=exc.message)
        boundary_diagnostic_log.log_event(boundary_diagnostic_log.Event.REFUSAL, disposition=body.disposition)
        return JSONResponse(status_code=408, content=body.model_dump())

    @app.get("/d/{deployment}/health", response_model=HealthResponse)
    def health(deployment: str) -> Response:
        cfg, err = _resolve_deployment(configs, deployment)
        if err is not None:
            return err
        return HealthResponse(
            world=cfg.schema,
            service_principal=service_principal_name(cfg),
            capabilities=capability_manifest(cfg),
            # Row 173/row 318: the SAME module-global `_identity_enforcement_posture`
            # `configure_identity_enforcement` set once at startup from the multiplex TOML, and
            # the anonymous-write refusal (rung a, above) reads at request time -- one value, two
            # readers, never a second copy that could drift.
            identity_enforcement=_identity_enforcement_posture,
        )

    @app.get("/d/{deployment}/rows/current")
    def rows_current(deployment: str, after_id: int = 0, limit: int = 100,
                      include_superseded: str = "") -> Response:
        cfg, err = _resolve_deployment(configs, deployment)
        if err is not None:
            return err
        if limit < 1 or limit > 1000:
            return JSONResponse(status_code=422, content={
                "detail": "limit must be between 1 and 1000 (transport-level bound, ADR-0002)"})
        # A4.2: after_id's domain closes symmetrically -- 0 <= after_id <= MAX_ID (the A2.6
        # lower-bound precedent, completed upward).
        oor = _out_of_range_id("after_id", after_id)
        if oor is not None:
            return oor
        # Ledger row 154 (rows-bulk-superseded-read): ONE new, opt-in, strictly-typed query
        # param -- default omitted/"" behavior is BYTE-IDENTICAL to pre-this-build (same
        # `ledger_current` query below, unchanged), never silently widened. `_strict_bool_flag`
        # is the ONE parser for this closed true/false/omitted vocabulary (ADR-0012 P1); an
        # illegal spelling 422s here, before any query runs.
        want_superseded, bad_flag = _strict_bool_flag("include_superseded", include_superseded)
        if bad_flag is not None:
            return bad_flag
        if not want_superseded:
            rows = _query_json(
                cfg,
                f"SELECT coalesce(jsonb_agg(t ORDER BY t.id), '[]'::jsonb) FROM "
                f"(SELECT * FROM {cfg.schema}.ledger_current WHERE id > {after_id} "
                f"ORDER BY id LIMIT {limit}) t;",
            )
            return JSONResponse(content=rows)
        # `include_superseded=true`: reads the RAW `ledger` table (record semantics, every row
        # ever written, current or superseded -- the same raw-table read `rows_asof` below
        # already uses one route over) rather than the `ledger_current` view, so a superseded
        # row is no longer structurally excluded. Superseded-ness is made legible PER ROW via
        # `is_current` -- derived from the EXACT predicate `ledger_current`'s own view
        # definition already commits to (`NOT EXISTS (SELECT 1 FROM ledger s WHERE s.supersedes
        # = l.id)`), the SAME correlated-subquery shape `rows_asof` and kernel/lineage's own
        # `countersigned_in_force`/`ledger_current` views already use -- never a new, boundary-
        # invented notion of "current" (ADR-0012 P2: the boundary derives, it does not author a
        # second truth). A panel toggling current-vs-superseded reads this one field; no second
        # query is needed to tell the two apart.
        rows = _query_json(
            cfg,
            f"SELECT coalesce(jsonb_agg(t ORDER BY t.id), '[]'::jsonb) FROM "
            f"(SELECT l.*, NOT EXISTS (SELECT 1 FROM {cfg.schema}.ledger s "
            f"WHERE s.supersedes = l.id) AS is_current "
            f"FROM {cfg.schema}.ledger l WHERE l.id > {after_id} "
            f"ORDER BY l.id LIMIT {limit}) t;",
        )
        return JSONResponse(content=rows)

    @app.get("/d/{deployment}/rows/{row_id}")
    def row_by_id(deployment: str, row_id: int) -> Response:
        cfg, err = _resolve_deployment(configs, deployment)
        if err is not None:
            return err
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

    @app.get("/d/{deployment}/rows/{row_id}/history")
    def row_history(deployment: str, row_id: int, after_id: int = 0, limit: int = HISTORY_DEFAULT_LIMIT) -> Response:
        cfg, err = _resolve_deployment(configs, deployment)
        if err is not None:
            return err
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

    @app.get("/d/{deployment}/credited")
    def credited(deployment: str, after_id: int = 0, limit: int = 100) -> Response:
        cfg, err = _resolve_deployment(configs, deployment)
        if err is not None:
            return err
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

    @app.get("/d/{deployment}/standing/principals")
    def standing_principals(deployment: str, after_id: int = 0, limit: int = 100) -> Response:
        cfg, err = _resolve_deployment(configs, deployment)
        if err is not None:
            return err
        # Hazard fixed in reach (legacy-led-retirement inventory pass, ledger row 1149): this
        # gate used to probe `principal_relations` (s41-only) even though the view THIS route
        # actually queries, `principal_standing_current`, is defined by s40 alone (kernel/
        # lineage/s40-principal-identity-events.sql line ~612) -- an s40-only, pre-s41 kernel
        # was spuriously refused here even though the object this route serves exists and is
        # perfectly queryable. Gate on the object this route actually reads.
        if not _regclass_exists(cfg, f"{cfg.schema}.principal_standing_current"):
            return capability_absent(
                "s40-identity",
                "This world carries no principal-identity views "
                "(kernel/lineage/s40-principal-identity-events.sql) -- "
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

    @app.get("/d/{deployment}/work/items")
    def work_items(deployment: str, after_slug: str = "", limit: int = 100, after_id: int | None = None) -> Response:
        cfg, err = _resolve_deployment(configs, deployment)
        if err is not None:
            return err
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

    @app.get("/d/{deployment}/views/{view}")
    def views_view(deployment: str, view: str, after_id: int = 0, after_slug: str = "",
                    after_tie: str = "", limit: int = 100) -> Response:
        # design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md mechanism item 1: the derived-read carrier.
        # `{view}` is checked against the CLOSED, spec-enumerated VIEW_REGISTRY before this
        # deployment's own kernel is ever touched -- an unknown view name is refused (404)
        # without a single query, exactly like `unknown_deployment`'s own posture.
        cfg, err = _resolve_deployment(configs, deployment)
        if err is not None:
            return err
        entry = VIEW_REGISTRY.get(view)
        if entry is None:
            return unknown_view(view)
        key_col, key_kind, key_unique = entry
        if view in _ROLE_CENSUS_DERIVED_VIEWS:
            # `work_role_census` names no stored relation (`_view_from_clause`'s own docstring) --
            # object/column existence checks against `{schema}.{view}` would themselves 404 on a
            # relation that was never supposed to exist. Gate on the underlying capability its
            # OWN body depends on instead: `work_item_current` (s22_work), the same object this
            # view's `opened`/`claims`/`closed` CTEs all key off (kernel/lineage/
            # s22-work-item-ledger.sql). `review_detail` predates s22 (s15, the base schema) so it
            # is never the gating fact.
            if not _regclass_exists(cfg, f"{cfg.schema}.work_item_current"):
                return capability_absent(
                    f"view:{view}:s22_work",
                    f"GET /views/{view} derives from this world's work-item ledger kinds "
                    f"(work_opened/work_claimed/work_closed) -- this world carries no "
                    f"{cfg.schema}.work_item_current object, so its lineage predates s22 "
                    f"(kernel/lineage/s22-work-item-ledger.sql) and this read is refused rather "
                    f"than served against a capability this world's kernel does not have.")
        else:
            if not _regclass_exists(cfg, f"{cfg.schema}.{view}"):
                return capability_absent(
                    f"view:{view}",
                    f"This world carries no {cfg.schema}.{view} object -- GET /views/{view} is "
                    f"refused rather than served from a relation this world's kernel does not "
                    f"have (object-existence detection, this service's own migrate-detect-drift "
                    f"discipline).")
            # The COLUMN-shape check, one level finer than the object-existence check just above:
            # `work_item_violations`/`work_review_gap`'s own key columns (target_id/slug) arrived
            # at later lineage deltas (s37/s29) than the views' own NAMES did -- a pre-that-delta
            # world carries a same-named view without the key column this route's pagination
            # needs, which would otherwise reach the SELECT below as a bare `column ... does not
            # exist` error (a genuinely typed, but needlessly coarse, `unclassified_failure` --
            # see `_column_exists`'s own docstring, live-witnessed against this repo's own
            # pre-s37 `autoharn1` world).
            if not _column_exists(cfg, cfg.schema, view, key_col):
                return capability_absent(
                    f"view:{view}:{key_col}",
                    f"This world's {cfg.schema}.{view} object exists but carries no {key_col!r} "
                    f"column -- this world's applied kernel lineage predates the delta that "
                    f"added it (column-shape detection, one level finer than object existence).")
        if limit < 1 or limit > 1000:
            return JSONResponse(status_code=422, content={
                "detail": "limit must be between 1 and 1000 (transport-level bound, ADR-0002)"})

        if key_unique:
            # UNIQUE-key view: BYTE-IDENTICAL to this route's pre-fix-round behavior (ledger
            # rows 153/154's own leading VIEW_REGISTRY comment has the full reasoning) -- ties
            # never occur on a genuinely unique key, so this is the OLD code path, untouched,
            # not routed through the new tiebreaker machinery at all. `after_tie` is meaningless
            # here and is never silently ignored (A10's own lesson, extended a third time).
            if after_tie:
                return JSONResponse(status_code=422, content={
                    "detail": f"after_tie is not accepted on GET /views/{view} -- this view's "
                              f"key ({view}.{key_col}) is unique per row, so no tiebreaker is "
                              f"ever needed; got after_tie={after_tie!r}"})
            if key_kind == "id":
                # The id-keyed pagination shape (A2.6/A4.2/A5.4): the SAME shape /rows/current
                # already uses, applied to this view's own key column. A supplied after_slug on
                # an id-keyed view is never silently ignored (A10's own lesson, applied a third
                # time).
                if after_slug:
                    return JSONResponse(status_code=422, content={
                        "detail": f"after_slug is not accepted on GET /views/{view} -- this view "
                                  f"pages on after_id (an id-shaped key, {view}.{key_col}); got "
                                  f"after_slug={after_slug!r}"})
                oor = _out_of_range_id("after_id", after_id)
                if oor is not None:
                    return oor
                rows = _query_json(
                    cfg,
                    f"SELECT coalesce(jsonb_agg(t ORDER BY t.{key_col}), '[]'::jsonb) FROM "
                    f"(SELECT * FROM {cfg.schema}.{view} WHERE {key_col} > {after_id} "
                    f"ORDER BY {key_col} LIMIT {limit}) t;",
                )
                return JSONResponse(content=rows)
            # key_kind == "slug": the A11 keyset shape /work/items already uses, applied to this
            # view's own text key column. A supplied after_id on a slug-keyed view is never
            # silently ignored either (A11 item 1's own precedent).
            if after_id:
                return JSONResponse(status_code=422, content={
                    "detail": f"after_id is not accepted on GET /views/{view} -- this view pages "
                              f"on after_slug (a text-shaped key, {view}.{key_col}); got "
                              f"after_id={after_id}, resupply as after_slug=<last-served-value> "
                              f"instead"})
            after_slug_bytes = len(after_slug.encode("utf-8"))
            if after_slug_bytes > MAX_AFTER_SLUG_BYTES:
                return JSONResponse(status_code=422, content={
                    "detail": f"after_slug must be at most {MAX_AFTER_SLUG_BYTES} bytes; got "
                              f"{after_slug_bytes} bytes"})
            repr_oor = _query_string_representability_failure("after_slug", after_slug)
            if repr_oor is not None:
                return repr_oor
            rows = _query_json(
                cfg,
                f"SELECT coalesce(jsonb_agg(t ORDER BY t.{key_col}), '[]'::jsonb) FROM "
                f"(SELECT * FROM {_view_from_clause(cfg, view)} WHERE {key_col} > :'after_slug' "
                f"ORDER BY {key_col} LIMIT {limit}) t;",
                extra_v={"after_slug": after_slug},
            )
            return JSONResponse(content=rows)

        # NON-UNIQUE key: the round-2 atomic-tie-group keyset (ledger rows 153/154 -- round 1's
        # CRITICAL finding fixed the plain-non-unique-key case; round 2's CRITICAL-adjacent
        # finding closed the byte-identical-row residual round 1 left open. See VIEW_REGISTRY's
        # own leading comment and `_nonunique_tie_group_sql`'s own docstring for the full
        # reasoning, including the mid-walk-append analysis and why a THIRD ordinal cursor
        # component is NOT used.). `_page_tie` is `md5(the row::text)`, carried through to the
        # served output as an extra field every non-unique-key view's response now legibly
        # carries -- the client-visible cursor contract change the fix round discloses, never
        # silent.
        tie_fmt_err = _composite_cursor_tie_format_failure("after_tie", after_tie)
        if tie_fmt_err is not None:
            return tie_fmt_err
        if key_kind == "id":
            if after_slug:
                return JSONResponse(status_code=422, content={
                    "detail": f"after_slug is not accepted on GET /views/{view} -- this view "
                              f"pages on after_id (an id-shaped key, {view}.{key_col}); got "
                              f"after_slug={after_slug!r}"})
            oor = _out_of_range_id("after_id", after_id)
            if oor is not None:
                return oor
            rows = _query_json(
                cfg,
                _nonunique_tie_group_sql(cfg.schema, view, key_col, str(after_id), limit),
                extra_v={"after_tie": after_tie},
            )
        else:
            # key_kind == "slug", non-unique.
            if after_id:
                return JSONResponse(status_code=422, content={
                    "detail": f"after_id is not accepted on GET /views/{view} -- this view pages "
                              f"on after_slug (a text-shaped key, {view}.{key_col}); got "
                              f"after_id={after_id}, resupply as after_slug=<last-served-value> "
                              f"instead"})
            after_slug_bytes = len(after_slug.encode("utf-8"))
            if after_slug_bytes > MAX_AFTER_SLUG_BYTES:
                return JSONResponse(status_code=422, content={
                    "detail": f"after_slug must be at most {MAX_AFTER_SLUG_BYTES} bytes; got "
                              f"{after_slug_bytes} bytes"})
            repr_oor = _query_string_representability_failure("after_slug", after_slug)
            if repr_oor is not None:
                return repr_oor
            rows = _query_json(
                cfg,
                _nonunique_tie_group_sql(cfg.schema, view, key_col, ":'after_slug'", limit),
                extra_v={"after_slug": after_slug, "after_tie": after_tie},
            )
        # MAX_TIE_GROUP_EXTRA_ROWS' own bound: a page legitimately exceeds `limit` ONLY by the
        # size of the byte-identical group straddling its own boundary (never for any other
        # reason -- `_nonunique_tie_group_sql`'s own docstring proves this). If that extension
        # is itself pathologically large, refuse loudly rather than serve it.
        if isinstance(rows, list) and len(rows) > limit:
            extra = len(rows) - limit
            if extra > MAX_TIE_GROUP_EXTRA_ROWS:
                return _tie_group_too_large(view, extra)
        return JSONResponse(content=rows)

    @app.get("/d/{deployment}/rows/asof/{ts}")
    def rows_asof(deployment: str, ts: str, after_id: int = 0, limit: int = 100) -> Response:
        # design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md mechanism item 2: the as-of reconstruction,
        # serving asof-export.tmpl's own "THE QUERY" (that file's module docstring) over HTTP.
        # `{ts}` is a typed ISO-8601 timestamp, refused typed 422 BEFORE any kernel call on
        # malformed input (the amendment spec's own words) -- `datetime.fromisoformat` is the
        # standard-library ISO-8601 parser; Python 3.11+ accepts the full profile including a
        # trailing 'Z'. This is DELIBERATELY STRICTER than asof-export.tmpl's own `--asof`
        # (which accepts anything postgres's timestamptz cast honors, e.g. a bare
        # '2026-07-18 10:23:00' with a space) -- the amendment spec's own choice, not softened
        # here; a caller wanting the looser CLI grammar uses the ./legacy/ original.
        cfg, err = _resolve_deployment(configs, deployment)
        if err is not None:
            return err
        try:
            parsed = datetime.datetime.fromisoformat(ts)
        except ValueError:
            return JSONResponse(status_code=422, content={
                "detail": f"ts must be a valid ISO-8601 timestamp (Python's own "
                          f"datetime.fromisoformat grammar); got {ts!r}"})
        # A representability check is deliberately NOT repeated here (A12's own discipline,
        # applied honestly rather than mechanically): a string that survives
        # datetime.fromisoformat cannot carry a U+0000 or an unpaired UTF-16 surrogate -- ISO-8601
        # is a closed character class ([0-9:+\-.TZ ]) neither of those failure modes can hide in,
        # so the check would be dead code, not defense in depth.
        if limit < 1 or limit > 1000:
            return JSONResponse(status_code=422, content={
                "detail": "limit must be between 1 and 1000 (transport-level bound, ADR-0002)"})
        oor = _out_of_range_id("after_id", after_id)
        if oor is not None:
            return oor
        # THE QUERY: asof-export.tmpl's own reconstruction, byte-identical in shape (one conjunct
        # on each side of ledger_current's own NOT EXISTS), served over `l.*` ONLY -- matching
        # every OTHER row-level route in this service (none of them join in `actor_name`; that
        # enrichment is asof-export.tmpl's OWN CLI-side presentation concern, not a kernel-view
        # fact this boundary adds truth of its own to serve -- spec §5, "no truth of its own").
        # `ts` crosses as a BOUND -v argument (:'asof'::timestamptz), never spliced -- the same
        # injection-safe substitution every other string-typed value in this service already uses.
        rows = _query_json(
            cfg,
            f"SELECT coalesce(jsonb_agg(t ORDER BY t.id), '[]'::jsonb) FROM "
            f"(SELECT l.* FROM {cfg.schema}.ledger l "
            f"WHERE l.ts <= :'asof'::timestamptz AND l.id > {after_id} "
            f"AND NOT EXISTS (SELECT 1 FROM {cfg.schema}.ledger s "
            f"WHERE s.supersedes = l.id AND s.ts <= :'asof'::timestamptz) "
            f"ORDER BY l.id LIMIT {limit}) t;",
            extra_v={"asof": parsed.isoformat()},
        )
        return JSONResponse(content=rows)

    @app.get("/d/{deployment}/meta", response_model=MetaResponse)
    def meta(deployment: str) -> Response:
        # design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md mechanism item 3: the capability surface a
        # rebased CLI shim decides its own behavior from -- see `_lineage_head`'s own docstring
        # for why its DB-touching half is reimplemented against this module's own `_psql` rather
        # than reusing migrate_core.py's bare, ungated runner.
        cfg, err = _resolve_deployment(configs, deployment)
        if err is not None:
            return err
        return MetaResponse(
            known_views=sorted(VIEW_REGISTRY),
            lineage_head=_lineage_head(cfg),
            boundary_version=BOUNDARY_SERVICE_VERSION,
            max_tie_group_extra_rows=MAX_TIE_GROUP_EXTRA_ROWS,
            max_sse_clients=_max_sse_clients,
            sse_poll_interval_secs=_sse_poll_interval_secs,
        )

    @app.get("/d/{deployment}/kinds", response_model=KindsResponse)
    def kinds(deployment: str) -> Response:
        # Ledger row 1480 (maintainer ruling on row 1479's finding): restores, on THIS served
        # transport, the valid-kinds TEACHING the legacy direct-psql `led` gave on a
        # `ledger_kind_check` refusal -- SSOT is the kernel's own live constraint (see
        # `_kind_vocabulary`'s own docstring for the exact query and why this is a dedicated
        # route rather than a VIEW_REGISTRY entry or a `/meta` field). No capability gate: unlike
        # `/credited` (s44) or `/standing/principals` (s40), `ledger_kind_check` has carried this
        # exact name since s15 (this repo's very first lineage delta with a `ledger` table) --
        # every deployment this service could serve carries it, so there is no "world predates
        # this delta" leg to gate on; `_kind_vocabulary`'s own empty-list fallback is the honest
        # answer for the deployment shape that somehow lacks it, not a capability_absent refusal.
        cfg, err = _resolve_deployment(configs, deployment)
        if err is not None:
            return err
        return KindsResponse(
            kinds=_kind_vocabulary(cfg),
            boundary_version=BOUNDARY_SERVICE_VERSION,
        )

    @app.get("/d/{deployment}/attestation", response_model=AttestationResponse)
    def attestation(deployment: str) -> Response:
        """Work item boundary-verdict-read-surface (row 221): serves the LATEST BANKED result
        of each independent instrument (verify-chain, judge, doctor) labeled as THIS SERVICE'S
        OWN last-known attestation -- serving/README.md's two-trust-roots section, verbatim:
        "never a substitute for running the independent instrument, and never conflated with
        it." NEVER runs verify-chain/judge/doctor itself (that would reopen exactly the
        second-trust-root hazard the README section this route implements exists to avoid) --
        this route only reads what one of THOSE THREE has already written to disk, if anything.

        Investigated, not assumed (`boundary_models.py`'s own module-level note above has the
        full account): `judge` genuinely banks -- the LIBRARY (`engine/ledger_differential.py`'s
        bare CLI) treats `--retain` as opt-in, but THIS REPO'S OWN operator verb
        (`bootstrap/templates/judge.tmpl`, its own header, verbatim: "the ordinary run: retain
        DerivationRecords") hardcodes `--retain` -- for `./autoharn judge`, retention IS the
        ordinary run, not an opportunistic extra (fix-round MODERATE, corrected from this
        route's own first-cut teach-text, which had it backwards). `verify-chain` and `doctor`
        bank NOTHING today (both templates read in full, no write-to-disk found in either) -- so
        those two classes always resolve to `NoBankedArtifact` in THIS build, an honest,
        disclosed fact, not a bug in this route.

        Deployment validation only (`_resolve_deployment`, the same discriminator gate every
        other route enforces) -- the payload itself does NOT vary by `{deployment}`
        (`AttestationResponse`'s own docstring: judge's bank is repo-checkout-relative, one
        process serving N deployments shares one bank)."""
        cfg, err = _resolve_deployment(configs, deployment)
        if err is not None:
            return err
        judge_derivation = _latest_judge_derivation()
        judge_field: BankedJudgeVerdict | NoBankedArtifact
        if judge_derivation is not None:
            judge_field = BankedJudgeVerdict(**judge_derivation)
        else:
            judge_field = NoBankedArtifact(
                # `--retain` omitted deliberately (fix-round MODERATE): for THIS repo's own
                # operator verb, bootstrap/templates/judge.tmpl hardcodes --retain and calls
                # that its "ordinary run" (that file's own header, verbatim) -- the flag is
                # redundant to name here, and naming it would (falsely) suggest an ordinary
                # `./autoharn judge` invocation needs an extra flag to bank anything.
                would_produce="./autoharn judge [target...]",
                message="no derivation.json found under engine/docs/ledger-marriage/derivations/ "
                        "(or its four differential-family subtrees) -- this repo's own "
                        "./autoharn judge retains a DerivationRecord on every ordinary run "
                        "(bootstrap/templates/judge.tmpl hardcodes --retain), so this checkout "
                        "simply has not run judge at all yet, not merely run it without "
                        "retention.")
        # verify-chain and doctor bank NOTHING in this codebase as it stands (confirmed by
        # reading both templates in full, module-level note above) -- always the typed absence,
        # honestly, never a live re-run to manufacture a "present" answer this route does not
        # have (row 221's own instruction: "NEVER runs the instrument server-side").
        verify_chain_field: BankedVerifyChainVerdict | NoBankedArtifact = NoBankedArtifact(
            would_produce="./autoharn verify-chain",
            message="verify-chain prints its reconciliation result to stdout only -- this "
                    "codebase's own verify-chain.tmpl has no write-to-disk of its own result "
                    "(the operator's signed-genesis ceremony redirects stdout to a file BY HAND "
                    "for GPG signing, a location this service cannot discover or trust as "
                    "'the latest verdict'); nothing is banked for this route to serve.")
        doctor_field: BankedDoctorSummary | NoBankedArtifact = NoBankedArtifact(
            would_produce="./autoharn doctor",
            message="doctor prints its PASS/FAIL/SKIP report to stdout only -- this codebase's "
                    "own doctor.tmpl has no write-to-disk of its own report; nothing is banked "
                    "for this route to serve.")
        return AttestationResponse(
            verify_chain=verify_chain_field, judge=judge_field, doctor=doctor_field)

    @app.get("/d/{deployment}/events")
    async def events(deployment: str, request: Request, after_head: int = 0) -> Response:
        """design/FABLE-BOUNDARY-SSE-EVENTS-SPEC.md: `GET /d/{deployment}/events`,
        `text/event-stream` -- a HEAD-ADVANCEMENT-ONLY push signal (spec §1), never a second
        data/pagination contract (spec §2: "no row payloads ... no kernel trigger"). `async def`,
        the ONE exception to this file's plain-`def` read-route convention -- this route never
        calls `_psql` itself (only the shared `_SseHub`'s own watcher does, briefly, per poll
        cycle) and must stay on the event loop for its whole open-ended lifetime, so there is no
        blocking-subprocess-on-the-threadpool hazard A3.1's plain-`def` rule exists to avoid.

        RESUME (spec §1 item 2): `Last-Event-ID` (the standard SSE reconnect header) takes
        precedence over the `?after_head=` query parameter when both are present -- a
        reconnecting browser `EventSource` sets the header automatically from the last event ID
        it saw, which is the more authoritative signal of the two when a caller supplies both.

        ADMISSION (spec §1 item 4): checked HERE, at connect time, against `_max_sse_clients` --
        this deployment's OWN `cfg`/`_psql`-gated admission (`MAX_INFLIGHT_KERNEL_CALLS`/
        `MAX_INFLIGHT_PER_DEPLOYMENT`) is NEVER consulted for this route's own connection (spec
        §1 item 4, verbatim: "must NOT occupy the 24-slot inflight admission gate"); the ONLY
        `_psql` call this connection's own lifetime touches is `_SseHub.connect`'s one immediate
        catch-up poll, which DOES pass through those gates like any other kernel read (see
        `_sse_query_head`'s own docstring) -- a saturated deployment there degrades to "no new
        information yet", never refuses the SSE connection itself.

        RESTART (spec §1 item 5, stated here per the spec's own instruction "say so in the
        route's own docstring so nobody 'improves' it into a drain exception"): `autoharn service
        restart` SIGTERMs this process; every open SSE connection, this one included, dies with
        it -- deliberately. This route adds NOTHING to the restart path. The client's own resume
        contract (above) makes reconnection lossless, so there is no drain/grace exception to
        add here, and none should be."""
        cfg, err = _resolve_deployment(configs, deployment)
        if err is not None:
            return err
        last_event_id = request.headers.get("last-event-id")
        if last_event_id is not None:
            try:
                resume_from = int(last_event_id)
            except ValueError:
                return JSONResponse(status_code=422, content={
                    "detail": f"Last-Event-ID must be an integer head id; got {last_event_id!r}"})
        else:
            resume_from = after_head
        oor = _out_of_range_id("after_head (or Last-Event-ID)", resume_from)
        if oor is not None:
            return oor
        # Spec §1 item 4: THIS hub-wide bound, counted across every subscriber of every
        # deployment on this process (the spec's own "per hub" phrasing) -- never the 24-slot
        # `MAX_INFLIGHT_KERNEL_CALLS` gate every OTHER route lives under. Total across
        # `sse_hubs` (a plain sum over each hub's own live subscriber count -- no separate
        # counter to keep in sync, ADR-0012 P1) rather than per-deployment, matching the spec's
        # own wording exactly.
        total_subscribers = sum(len(h.subscribers) for h in sse_hubs.values())
        if total_subscribers >= _max_sse_clients:
            return sse_saturated(
                _max_sse_clients,
                f"this hub already has MAX_SSE_CLIENTS={_max_sse_clients} concurrent SSE "
                f"connections open (design/FABLE-BOUNDARY-SSE-EVENTS-SPEC.md §1 item 4 -- its "
                f"own bound, never the inflight kernel-call gate) -- refused immediately rather "
                f"than queued. Retry after a short backoff.")
        hub = sse_hubs[cfg.name]

        async def _stream():
            # row-429/sse-subscriber-slot-leak: `hub.connect(queue)` now runs INSIDE this
            # try/finally (it used to run before it, unguarded) -- `connect()` itself is now
            # cancellation-safe on its own (see its docstring: the one `await` it makes runs
            # BEFORE registration), but registering here too means a cancellation delivered
            # anywhere else in this generator's body -- between `connect()` returning and the
            # `try:` line used to not exist as a gap, but any future edit that adds one is now
            # guarded structurally rather than by review -- still always reaches `disconnect()`,
            # which is itself safe to call on a queue `connect()` never actually registered.
            # row-554/hub-shutdown-drain-hang: `queue` also carries `_SSE_SHUTDOWN_SENTINEL`
            # (never a real head id -- see that name's own docstring) -- the type hint below
            # stays documentation-only (Python does not enforce it at runtime; widening it to
            # `int | object` would just restate this same comment in typing form).
            queue: asyncio.Queue[int] = asyncio.Queue()
            try:
                known_head = await hub.connect(queue)
                last_sent = resume_from
                if known_head > last_sent:
                    yield f"event: head\ndata: {json.dumps({'head_id': known_head})}\n\n"
                    last_sent = known_head
                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        new_head = await asyncio.wait_for(
                            queue.get(), timeout=SSE_KEEPALIVE_INTERVAL_S)
                    except asyncio.TimeoutError:
                        yield ": keepalive\n\n"
                        continue
                    # row-554: the shutdown broadcast (`_BoundaryUvicornServer.shutdown`) --
                    # spec §1 item 5, "connections die at restart ON PURPOSE" -- exit NOW,
                    # never yielding another event; checked by identity, never `>`, since this
                    # sentinel is not an int and a real head id is never this exact object.
                    if new_head is _SSE_SHUTDOWN_SENTINEL:
                        break
                    if new_head > last_sent:
                        yield f"event: head\ndata: {json.dumps({'head_id': new_head})}\n\n"
                        last_sent = new_head
            finally:
                await hub.disconnect(queue)

        return StreamingResponse(
            _stream(), media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

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
        def handler(deployment: str, request: Request, raw_body: bytes = Depends(_bounded_raw_body)) -> Response:
            cfg, err = _resolve_deployment(configs, deployment)
            if err is not None:
                return err
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
            # explicit call is where ALL three A3.2 axes are caught -- encoding
            # (UnicodeDecodeError, a ValueError subclass), value (an oversized integer literal,
            # ValueError), and structure (JSONDecodeError, also ValueError; or RecursionError on
            # deep nesting, which subclasses RuntimeError -- exactly why the app's infra handler
            # is narrowed to PsqlInfraFailure and cannot accidentally swallow this). Routed
            # through `_guard_recursion` (row 1628's single guarded-traversal helper) with
            # ValueError explicitly folded in alongside RecursionError -- `_classify_parse_failure`
            # already gives both exception families the same typed-422 treatment here. Never
            # echoes raw_body back to the client.
            if raw_body:
                payload, axis, detail = _guard_recursion(
                    json.loads, raw_body, exceptions=(ValueError, RecursionError))
                if axis is not None:
                    return JSONResponse(status_code=422, content={
                        "detail": f"malformed write payload -- {axis} axis: {detail}"})
            else:
                payload = None
            if not isinstance(payload, dict):
                return JSONResponse(status_code=422, content={
                    "detail": "write payload must be a JSON object (transport-level shape check, spec §4)"})

            minted_conflict = _apply_minted_actor(payload)
            if minted_conflict is not None:
                return minted_conflict

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
            # HERE, after parse, rather than inside json.loads. Routed through the SAME
            # `_guard_recursion` helper (row 1628) A3.2/A13 above use -- same classifier, same
            # typed-422 shape, same structure axis -- because to the caller this is observably
            # the same "body nests too deeply" class, just a different Python frame overflowing
            # first.
            repr_detail, axis, detail = _guard_recursion(_representability_axis_failure, payload)
            if axis is not None:
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
            # Diagnostic-logging spec §5 emission site (c): the verdict/refusal classification
            # path -- kernel.write_verdict's own shape (kernel/lineage/
            # s43-typed-verdict-write-boundary.sql: disposition/row_id/refusal_id/sqlstate/
            # message) is read verbatim here, never a second copy of its field names. The join
            # anchor is `refusal_id` (the committed write_refused row's own id), NEVER the
            # payload digest -- row-1498's witness (boundary_diagnostic_log's own module
            # docstring; design/FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md §1 point 1) found the
            # kernel's canonical-jsonb-text digest and this service's own `json.dumps` digest
            # UNEQUAL by mechanism (key-order normalization differs) -- so a digest was never a
            # sound join key to log in the first place.
            v_disposition = verdict.get("disposition") if isinstance(verdict, dict) else None
            v_row_id = verdict.get("row_id") if isinstance(verdict, dict) else None
            v_refusal_id = verdict.get("refusal_id") if isinstance(verdict, dict) else None
            boundary_diagnostic_log.log_event(
                boundary_diagnostic_log.Event.WRITE_VERDICT, surface=surface,
                disposition=v_disposition, row_id=v_row_id, refusal_id=v_refusal_id)
            # Kernel verdicts (accepted AND refused) cross byte-verbatim as HTTP 200 -- a
            # kernel refusal is a first-class domain RESULT, not a transport error (spec §4).
            return JSONResponse(status_code=200, content=verdict)
        handler.__name__ = f"write_{surface}"
        return handler

    for surface, fn in WRITE_SURFACES.items():
        app.add_api_route(f"/d/{{deployment}}/write/{surface}", make_write_route(surface, fn), methods=["POST"])

    def _artifact_capability_absent(cfg: BoundaryConfig) -> JSONResponse | None:
        """design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part B: the SAME s43-capability-manifest
        idiom `make_write_route`'s own handler uses (`prosecdef` existence probe), applied to
        `kernel.artifact_write` -- a world without s51 applied refuses all three artifact routes
        typed, never falls back to any other path."""
        if bool(_query_json(
            cfg,
            f"SELECT to_jsonb(EXISTS (SELECT 1 FROM pg_proc p JOIN pg_namespace n "
            f"ON n.oid = p.pronamespace WHERE n.nspname = '{cfg.kern}' "
            f"AND p.proname = 'artifact_write' AND p.prosecdef));",
        )):
            return None
        return capability_absent(
            "s51-artifact-store",
            "This world carries no s51 artifact store (kernel.artifact_write absent) -- the "
            "artifact routes refuse entirely rather than falling back to any other path "
            "(design/FABLE-ARTIFACT-STORE-SPEC.md; design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md "
            "Part B).")

    def _bad_artifact_hash(h: str) -> JSONResponse:
        return JSONResponse(status_code=422, content={
            "detail": f"artifact hash {h!r} is not a well-formed 64-lowercase-hex-char SHA-256 "
                      f"digest (kernel/lineage/s51-artifact-store.sql: hash is the artifact "
                      f"table's own PK, always lowercase hex)."})

    @app.get("/d/{deployment}/artifacts/{hash}")
    def artifact_get(deployment: str, hash: str) -> Response:
        """design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part B, route 1: content, streamed as the
        artifact's own stored media_type -- not wrapped in a JSON envelope (the legacy CLI's own
        `led artifact get` writes bytes to a file/stdout directly; this route mirrors that shape
        rather than forcing every caller through a base64 JSON decode for what is, on the wire,
        already raw content). Server-side hash re-verification on the way OUT (mirroring the
        legacy CLI's own WA6 corruption-drill discipline, s51-artifact-store.sql's spec: "a
        corrupt store must fail loud, never serve silently wrong bytes") -- belt-and-braces with
        any client-side re-check the rebased CLI shim also performs."""
        cfg, err = _resolve_deployment(configs, deployment)
        if err is not None:
            return err
        if not _ARTIFACT_HASH_RE.match(hash):
            return _bad_artifact_hash(hash)
        cap_err = _artifact_capability_absent(cfg)
        if cap_err is not None:
            return cap_err
        row = _query_json(
            cfg,
            f"SELECT to_jsonb(t) FROM (SELECT encode(bytes,'base64') AS b64, media_type "
            f"FROM {cfg.kern}.artifact WHERE hash = '{hash}') t;")
        if row is None:
            return JSONResponse(status_code=404, content={
                "detail": f"no artifact registered with hash {hash!r}."})
        raw = base64.b64decode(row["b64"])
        computed = hashlib.sha256(raw).hexdigest()
        if computed != hash:
            return JSONResponse(status_code=500, content={
                "detail": f"CORRUPT STORE -- the bytes stored for hash {hash!r} do NOT hash to "
                          f"it (computed {computed!r} instead); kernel/lineage/"
                          f"s51-artifact-store.sql: a corrupt store fails loud here, never "
                          f"serves silently-wrong bytes under a claimed hash. Nothing served."})
        return Response(content=raw, media_type=row["media_type"])

    @app.get("/d/{deployment}/artifacts/{hash}/stat")
    def artifact_stat(deployment: str, hash: str) -> Response:
        """design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part B, route 2: metadata only, no bytes --
        mirrors `led artifact stat`'s own legacy shape (hash, size, media_type, registered_at,
        registered_by NAME)."""
        cfg, err = _resolve_deployment(configs, deployment)
        if err is not None:
            return err
        if not _ARTIFACT_HASH_RE.match(hash):
            return _bad_artifact_hash(hash)
        cap_err = _artifact_capability_absent(cfg)
        if cap_err is not None:
            return cap_err
        row = _query_json(
            cfg,
            f"SELECT to_jsonb(t) FROM (SELECT a.hash, a.size, a.media_type, a.registered_at, "
            f"p.name AS registered_by FROM {cfg.kern}.artifact a "
            f"LEFT JOIN {cfg.kern}.principal p ON p.id = a.registered_by "
            f"WHERE a.hash = '{hash}') t;")
        if row is None:
            return JSONResponse(status_code=404, content={
                "detail": f"no artifact registered with hash {hash!r}."})
        return JSONResponse(content=row)

    def artifact_put(deployment: str, request: Request, raw_body: bytes = Depends(_bounded_artifact_body)) -> Response:
        """design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part B, route 3: register bytes.
        DELIBERATELY NOT built from `make_write_route` (that helper's transport -- a psql `-v`
        execve argument, bounded by MAX_PSQL_ARG_BYTES=100000 -- is exactly the wall
        kernel/lineage/s51-artifact-store.sql's own header names as too small for a base64
        artifact payload; see `_query_json_stdin_var`'s own docstring). This handler runs the
        SAME parse-closure/value-closure/id-domain checkpoints `make_write_route` does, in the
        SAME order, then hands the re-serialized payload to psql via a server-side tempfile
        instead of an argv slot -- no MAX_PSQL_ARG_BYTES checkpoint applies here (P1: the
        kernel's own 1 MiB cap, verified server-side inside kernel.artifact_write, is the ONLY
        size authority; this route imposes no second one)."""
        cfg, err = _resolve_deployment(configs, deployment)
        if err is not None:
            return err
        cap_err = _artifact_capability_absent(cfg)
        if cap_err is not None:
            return cap_err
        if raw_body:
            payload, axis, detail = _guard_recursion(
                json.loads, raw_body, exceptions=(ValueError, RecursionError))
            if axis is not None:
                return JSONResponse(status_code=422, content={
                    "detail": f"malformed write payload -- {axis} axis: {detail}"})
        else:
            payload = None
        if not isinstance(payload, dict):
            return JSONResponse(status_code=422, content={
                "detail": "write payload must be a JSON object (transport-level shape check, spec §4)"})
        # design/FABLE-DISPATCH-MECHANICS-SPEC.md §2/§3: same minted-principal `actor` rule as
        # `make_write_route` above (ADR-0012 P1: one rule, not a per-route dialect).
        minted_conflict = _apply_minted_actor(payload)
        if minted_conflict is not None:
            return minted_conflict
        int_field_oor = _bound_write_payload_ints("artifact", payload)
        if int_field_oor is not None:
            return int_field_oor
        payload_json, reser_axis, reser_detail = _reserialize_or_value_axis_failure(payload)
        if payload_json is None:
            return JSONResponse(status_code=422, content={
                "detail": f"malformed write payload -- {reser_axis} axis: {reser_detail}"})
        repr_detail, axis, detail = _guard_recursion(_representability_axis_failure, payload)
        if axis is not None:
            return JSONResponse(status_code=422, content={
                "detail": f"malformed write payload -- {axis} axis: {detail}"})
        if repr_detail is not None:
            return JSONResponse(status_code=422, content={
                "detail": f"malformed write payload -- representability axis: {repr_detail}"})
        # NO MAX_PSQL_ARG_BYTES checkpoint here -- see this function's own docstring; the payload
        # crosses to psql via a tempfile, never an argv slot.
        fd, tmp_path = tempfile.mkstemp(prefix="boundary-artifact-put-", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(payload_json)
            verdict = _query_json_stdin_var(
                cfg, "payload", tmp_path,
                f"SELECT to_jsonb(v) FROM {cfg.kern}.artifact_write(:'payload'::jsonb) v;")
        finally:
            os.unlink(tmp_path)
        # Diagnostic-logging spec §5 emission site (c), the artifact route's own instance --
        # see `make_write_route`'s handler for the shared reasoning (refusal_id, never the
        # payload digest, is the join anchor).
        v_disposition = verdict.get("disposition") if isinstance(verdict, dict) else None
        v_row_id = verdict.get("row_id") if isinstance(verdict, dict) else None
        v_refusal_id = verdict.get("refusal_id") if isinstance(verdict, dict) else None
        boundary_diagnostic_log.log_event(
            boundary_diagnostic_log.Event.WRITE_VERDICT, surface="artifact",
            disposition=v_disposition, row_id=v_row_id, refusal_id=v_refusal_id)
        return JSONResponse(status_code=200, content=verdict)

    app.add_api_route("/d/{deployment}/artifacts", artifact_put, methods=["POST"])

    return app


# The one free win the logging-direction survey identified (design/
# LOGGING-DIRECTION-SURVEY-2026-07-27.md §3.4 item 4, ledger row 1486): uvicorn's own default
# logging runs unmodified today (no `log_config`/`log_level` was ever passed to `uvicorn.Config`
# below) and lands in <world>/service.log via ensure_running.py's stdout/stderr redirect --
# WITNESSED there with zero timestamps, which made a real refusal ("wearing 200 OK") to a
# specific ledger row's 14:11 timestamp un-attributable without one. This constant's ONLY
# job is adding an ISO-8601 timestamp ahead of uvicorn's own default fields; nothing else about
# uvicorn's default format, level, or destination changes.
#
# MECHANISM (installed uvicorn 0.51's own documented mechanism, read from
# uvicorn/config.py's `Config.configure_logging`, not a web recollection): `Config(log_config=...)`
# is fed straight to `logging.config.dictConfig` when it is a dict (config.py ~line 391). The
# dict shape (`version`/`formatters`/`handlers`/`loggers`) is uvicorn's own `uvicorn.config.
# LOGGING_CONFIG` default, deep-copied here (never mutated in place -- that module-level dict is
# process-global and other code may still read it) so this restatement is a MINIMAL, CITED copy,
# not a re-derivation: same `uvicorn.logging.DefaultFormatter`/`AccessFormatter` classes, same
# message shapes (`%(levelprefix)s %(message)s` / `%(levelprefix)s %(client_addr)s - "%(request_
# line)s" %(status_code)s`), same handlers (stderr for `default`, stdout for `access`), same
# logger levels (`INFO`) and `propagate` flags -- only `%(asctime)s ` is prepended to each
# formatter's `fmt`, with `datefmt="%Y-%m-%dT%H:%M:%S%z"` (ISO-8601 basic format, local time with
# UTC offset, e.g. `2026-07-27T15:29:48+0200`). If a future uvicorn upgrade changes its own
# `LOGGING_CONFIG` defaults, this restatement of the OTHER keys (levels/handlers/classes) could
# drift out of sync with the new installed defaults -- disclosed here rather than silently
# assumed current; re-diff against `uvicorn.config.LOGGING_CONFIG` on any uvicorn version bump.
_UVICORN_LOG_CONFIG_WITH_ISO_TIMESTAMP: dict[str, Any] = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)
for _formatter in _UVICORN_LOG_CONFIG_WITH_ISO_TIMESTAMP["formatters"].values():
    _formatter["fmt"] = "%(asctime)s " + _formatter["fmt"]
    _formatter["datefmt"] = "%Y-%m-%dT%H:%M:%S%z"
del _formatter


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python3 -m serving.boundary_service",
        description="The FastAPI outer boundary into an autoharn-managed ledger, multiplexing "
                     "N deployments behind one process (design/"
                     "FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md; design/"
                     "FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md §3).")
    p.add_argument("--config", required=True,
                    help="path to boundary-multiplex.toml (spec §3) -- one operator-authored "
                         "file naming every deployment this process serves, each reachable at "
                         "/d/{name}/... A single-deployment config is the degenerate, expected "
                         "common case; it still requires exactly one [deployments.NAME] table "
                         "(no unprefixed-route mode survives -- spec §2).")
    p.add_argument("--host", default="127.0.0.1",
                    help="bind address for THIS HTTP service (default 127.0.0.1, loopback-only)")
    p.add_argument("--port", type=int, default=8420)
    p.add_argument("--i-understand-this-exposes-the-ledger", action="store_true",
                    help="required to bind any non-loopback address -- the ledger carries "
                         "operator-real content (spec §2, the OTel-collector localhost-only posture)")
    p.add_argument("--pidfile", default=None,
                    help="write THIS PROCESS's own pid to this path, but ONLY after this "
                         "process's own listen-socket bind has genuinely succeeded (design/"
                         "FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md §2, the pidfile-as-witness-of-bind "
                         "fix for the ensure-running TOCTOU). The bind happens HERE, synchronously, "
                         "before uvicorn/ASGI ever start (NOT via an ASGI 'startup' event -- the "
                         "installed uvicorn runs that event BEFORE its own socket bind, which "
                         "would make 'startup' fire for a losing racer too). Written by "
                         "libexec/autoharn-service's own spawn; harmless and unused for a manual "
                         "operator start that omits this flag.")
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
    # Multiplex spec §3: the WHOLE config validates before the socket ever binds -- unknown
    # keys anywhere, a missing required key, or zero deployments each refuse loudly BY NAME,
    # construction-time (ADR-0002 rung 1), never reaching uvicorn.run at all.
    try:
        records, log_level, identity_enforcement, sse_poll_interval_secs, max_sse_clients = (
            boundary_multiplex_config.load_multiplex_config_with_sse(args.config))
    except boundary_multiplex_config.MultiplexConfigError as e:
        sys.stderr.write(f"boundary_service: REFUSED at start-up (config) -- {e}\n")
        return 2
    # Diagnostic-logging spec §2 "Config": the level is already validated (whole-file, before
    # this point) by boundary_multiplex_config.py against boundary_diagnostic_log.LEVELS --
    # configure_level here is construction-time defense in depth, not the primary validation.
    boundary_diagnostic_log.configure_level(log_level)
    # design/FABLE-DISPATCH-MECHANICS-SPEC.md §3: same construction-time-defense-in-depth
    # pattern as log_level above -- already validated whole-file by boundary_multiplex_config.py.
    configure_identity_enforcement(identity_enforcement)
    # design/FABLE-BOUNDARY-SSE-EVENTS-SPEC.md §1 items 1/4: same construction-time-defense-in-
    # depth pattern -- already validated whole-file by boundary_multiplex_config.py.
    configure_sse_poll_interval(sse_poll_interval_secs)
    configure_max_sse_clients(max_sse_clients)
    # Multiplex spec §4: MAX_INFLIGHT_KERNEL_CALLS stays the GLOBAL bound; the per-deployment
    # sub-bound is computed ONCE here (never re-derived per request) and PRINTED at startup
    # (spec §4, verbatim) so an operator can see what their own deployment count produced.
    per_dep_limit = compute_per_deployment_limit(len(records))
    sys.stderr.write(
        f"boundary_service: MAX_INFLIGHT_KERNEL_CALLS={MAX_INFLIGHT_KERNEL_CALLS} (global) "
        f"MAX_INFLIGHT_PER_DEPLOYMENT={per_dep_limit} (per each of {len(records)} "
        f"deployment(s): {sorted(records.keys())}) MAX_SSE_CLIENTS={max_sse_clients} (per hub) "
        f"SSE_POLL_INTERVAL_SECS={sse_poll_interval_secs}\n")
    # Diagnostic-logging spec §2 L4/§5 emission site (d): the startup banner's own typed call
    # site, beside (not instead of) the pre-existing human stderr line directly above. Extra
    # fields beyond Event.STARTUP's own required set are permitted (log_event only enforces
    # PRESENCE of the required set, never a closed field list) -- additive, not a vocabulary
    # change.
    boundary_diagnostic_log.log_event(
        boundary_diagnostic_log.Event.STARTUP,
        deployments=sorted(records.keys()),
        max_inflight_kernel_calls=MAX_INFLIGHT_KERNEL_CALLS,
        max_inflight_per_deployment=per_dep_limit,
        log_level=log_level,
        identity_enforcement=identity_enforcement,
        max_sse_clients=max_sse_clients,
        sse_poll_interval_secs=sse_poll_interval_secs,
    )
    configs: dict[str, BoundaryConfig] = {}
    for name, record in records.items():
        configs[name] = BoundaryConfig(
            record,
            dep_semaphore=threading.BoundedSemaphore(per_dep_limit),
            dep_limit=per_dep_limit,
        )
    app = create_app(configs)
    if args.pidfile:
        # BIND-AS-LOCK, DONE HERE, SYNCHRONOUSLY, BEFORE UVICORN EVER STARTS (design/
        # FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md §2; round-1 review SEVERE-2 fix). An app-level
        # ASGI 'startup' event handler is NOT a safe place to detect bind success on the
        # installed uvicorn (0.51): reading `uvicorn.server.Server.startup`'s own source shows it
        # runs the ASGI lifespan 'startup' event BEFORE attempting its own socket bind -- so a
        # LOSING racer's app-level startup handler would still fire before that racer's own bind
        # ever failed, defeating the "reaching this handler proves ownership" reasoning entirely.
        # Binding the socket ourselves, here, sidesteps that ordering question altogether: this
        # bind() call itself IS the lock (the OS raises OSError immediately, deterministically, if
        # a sibling process already holds this exact host:port) -- there is no window between
        # "bind succeeded" and "pidfile written" that any async machinery (ASGI, uvicorn, or
        # otherwise) could ever violate, because this happens entirely before the ASGI world
        # starts.
        # SO_REUSEADDR IS set (needed for an honest restart shortly after real traffic: an
        # accepted connection's own TIME_WAIT state -- e.g. from a health-check probe -- otherwise
        # blocks rebinding the exact same listening port for a good while, live-witnessed against
        # this exact code). BUT bind() ALONE is not the exclusivity boundary once SO_REUSEADDR is
        # set: Linux permits a SECOND socket to bind() the same address:port successfully as long
        # as NEITHER has called listen() yet (live-witnessed round-1 review finding: two racing
        # bind() calls both succeeded here before this fix, because uvicorn/asyncio's own listen()
        # call happens well after this process's Python/FastAPI import overhead -- a wide-open
        # window). The actual lock is listen(): only ONE socket may hold the LISTEN state on a
        # given address:port even with SO_REUSEADDR set. So listen() is called HERE, synchronously,
        # immediately after bind() -- closing that window to zero -- and the pidfile is written
        # only once THIS process's own listen() has ALSO succeeded. Round-2 review MINOR fix:
        # asyncio's own later `create_server()` call on this already-listening socket is NOT a
        # harmless no-op re-application of the same backlog -- measured directly with `ss -ltn`
        # against a scratch service spawned via this exact code path, the requested backlog of
        # 2048 here reads back as 512 once uvicorn/asyncio has taken the socket over (asyncio's
        # `loop.create_server` calls `sock.listen()` again with its own default backlog, silently
        # overriding whatever this process asked for). Harmless for THIS module's purposes (this
        # backlog only bounds a burst of near-simultaneous inbound connections, and 512 is still
        # generous for a local single-boundary service), but it is a real, measured override, not
        # a no-op -- do not rely on the 2048 figure surviving past this point.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((args.host, args.port))
            sock.listen(2048)
        except OSError as e:
            sock.close()
            sys.stderr.write(
                f"boundary_service: REFUSED -- could not bind/listen on {args.host}:{args.port} "
                f"({e.__class__.__name__}: {e}) -- the port is genuinely held by another "
                f"process. Nothing was touched.\n")
            return 1
        # Bind+listen succeeded: THIS process, right now, provably holds the port. Write the
        # pidfile immediately and synchronously, before handing the socket to uvicorn at all --
        # O_CREAT|O_EXCL so a residual file at this exact path (a caller reusing a stale path is
        # its own bug) is never silently clobbered rather than surfaced.
        try:
            fd = os.open(args.pidfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            # Round-2 review MODERATE-silent fix, ROUND-4 REVIEW SEVERE-B (item 1) EXTENSION:
            # this branch means THIS process just won a real bind()+listen() -- it IS the
            # boundary, right now -- but a pidfile already sat at this exact path (an unrelated
            # leftover, a caller reusing a stale path, or a lost race against ensure_running.py's
            # own pre-unlink identity check). The round-2 fix only ever WARNED and left the stale
            # file untouched, unconditionally -- which is exactly the "stale-pidfile squat trap"
            # round-4 review's SEVERE-B finding named: `autoharn service stop` would act (or,
            # correctly, refuse to act) on whatever stale content sat there, while the REAL winner
            # -- this process -- served unrecorded, and the only truthful diagnostic was buried in
            # this stderr line, never reaching the pidfile itself.
            #
            # Fix: read the squatting content and ask the SAME identity question `stop` and
            # ensure_running.py's own pre-clear already ask -- is it a LIVE serving.boundary_
            # service process for THIS world's own --config? If the squatter is dead, unparseable,
            # or simply not a boundary_service at all, this pidfile is provably stale: reclaim it
            # ATOMICALLY (a tempfile in the SAME directory + os.replace, never a bare truncate-in-
            # place, so a reader never observes a half-written file) so `stop` targets the TRUE,
            # live winner instead of dead/wrong content. Only when the squatter IS a live
            # serving.boundary_service for this same toml -- a genuinely surprising case (this
            # process's own successful bind()+listen() proves nothing else holds THIS port, but
            # says nothing about a live sibling using the same toml against a different one) -- is
            # the file left untouched, warning exactly as the round-2 fix always did.
            try:
                squatting_content = Path(args.pidfile).read_text(encoding="utf-8")
            except OSError as read_err:
                squatting_content = f"<unreadable: {read_err.__class__.__name__}: {read_err}>"
            squatting_pid: int | None = None
            try:
                squatting_pid = int(squatting_content.strip())
            except ValueError:
                squatting_pid = None
            squatter_is_live_boundary_service = (
                squatting_pid is not None
                and ensure_running.pid_is_boundary_service(squatting_pid, Path(args.config))
            )
            if squatter_is_live_boundary_service:
                sys.stderr.write(
                    f"boundary_service: WARNING -- pidfile {args.pidfile} already existed "
                    f"(content: {squatting_content!r}) when this process (pid {os.getpid()}) won "
                    f"the bind()+listen() on {args.host}:{args.port}. The service IS up and "
                    f"correctly serving under pid {os.getpid()}, but that pid was NOT recorded -- "
                    f"the existing pidfile names pid {squatting_pid}, which IS a live "
                    f"serving.boundary_service process for this same --config, so it was left "
                    f"untouched rather than overwritten (never reclaim a pidfile that may "
                    f"legitimately belong to a live sibling). 'autoharn service stop' will act on "
                    f"the pidfile's OLD content, which is very likely wrong now for THIS process. "
                    f"Remedy: remove {args.pidfile} by hand and re-run with --pidfile once this "
                    f"process is confirmed healthy, or stop this pid ({os.getpid()}) directly.\n")
            else:
                tmp_fd, tmp_path = tempfile.mkstemp(
                    dir=str(Path(args.pidfile).parent), prefix=".autoharn-service.pid.")
                try:
                    with os.fdopen(tmp_fd, "w") as f:
                        f.write(str(os.getpid()))
                    os.replace(tmp_path, args.pidfile)
                except OSError:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                    raise
                sys.stderr.write(
                    f"boundary_service: RECLAIMED stale pidfile {args.pidfile} -- its previous "
                    f"content ({squatting_content!r}) was not a live serving.boundary_service "
                    f"process for this world's own --config {args.config} (dead pid, unparseable "
                    f"content, or an unrelated process -- PID REUSE can produce any of these). "
                    f"Rewrote it, atomically (tempfile + rename, never a bare truncate), to this "
                    f"process's own pid {os.getpid()}, which just won the real bind()+listen() on "
                    f"{args.host}:{args.port}. 'autoharn service stop' now targets the real "
                    f"winner.\n")
        else:
            with os.fdopen(fd, "w") as f:
                f.write(str(os.getpid()))
        # Hand the ALREADY-BOUND socket to uvicorn (the same `sockets=` pathway uvicorn's own
        # multi-worker/gunicorn integration uses) -- asyncio's own `create_server` calls
        # `sock.listen()` on it; uvicorn never re-binds host/port when a socket is supplied.
        # Row 554: `_BoundaryUvicornServer`, not a bare `uvicorn.Server` -- see that class's own
        # docstring (the SSE-shutdown-hang fix); `timeout_graceful_shutdown` is the defensive
        # backstop `_UVICORN_GRACEFUL_SHUTDOWN_TIMEOUT_S`'s own docstring explains.
        _BoundaryUvicornServer(uvicorn.Config(
            app, host=args.host, port=args.port,
            timeout_graceful_shutdown=_UVICORN_GRACEFUL_SHUTDOWN_TIMEOUT_S,
            log_config=_UVICORN_LOG_CONFIG_WITH_ISO_TIMESTAMP)).run(sockets=[sock])
        return 0
    # Row 554: same `_BoundaryUvicornServer` substitution as the --pidfile branch above --
    # `uvicorn.run(...)` is a convenience wrapper around exactly this Server-construct-then-run
    # shape (it builds a plain `uvicorn.Server` internally and offers no way to swap the class),
    # so this branch is spelled out rather than calling it, to carry the same fix. `try/except
    # KeyboardInterrupt: pass` matches `uvicorn.run()`'s own behavior (a manual operator run in
    # an interactive terminal, Ctrl-C, exits quietly rather than printing a traceback) --
    # everything else (host/port bind, no pre-bound socket, no pidfile) is unchanged.
    _no_pidfile_server = _BoundaryUvicornServer(uvicorn.Config(
        app, host=args.host, port=args.port,
        timeout_graceful_shutdown=_UVICORN_GRACEFUL_SHUTDOWN_TIMEOUT_S,
        log_config=_UVICORN_LOG_CONFIG_WITH_ISO_TIMESTAMP))
    try:
        _no_pidfile_server.run()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
