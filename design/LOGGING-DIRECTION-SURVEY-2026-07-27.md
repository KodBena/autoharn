# LOGGING-DIRECTION-SURVEY — the omega/proxy logging architecture and a suggested direction for autoharn

<!-- doc-attest-exempt: agent-authored survey report, filed verbatim by the orchestrator
2026-07-27 (maintainer commission, ledger row 1484; Opus exception maintainer-granted;
license fence per the commission's STEP 0, compliance statement in the report's own §0).
The maintainer has not yet read it. Removal condition: superseded by a ratified logging
spec that cites it.

Mechanical, content-preserving follow-up (diagnostic-logging build, same day): gates/
link_integrity.py refused this build's commit over three PRE-EXISTING broken markdown links
in this file, each targeting `../service.log` -- a gitignored, host-local runtime artifact
(`.gitignore:53`) that never exists in a fresh checkout, so the gate correctly flags any link
to it as broken regardless of which build touches the file next. The three link constructs
were converted to plain inline-code mentions with an inline note explaining why no link target
exists; no factual claim, witness-class marking, number, or the §0 compliance statement's
substance was altered by this pass -- a hazard found in reach of this build's own commit
attempt (CLAUDE.md's engineering-responsibility rule), fixed rather than routed around or
gate-skipped. -->
<!-- design-currency: status=historical superseded-by=FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md -->

This document is a survey of another codebase's logging design (the "proxy," a separate
project of the maintainer's, at `/home/bork/w/omega/proxy`) written to inform a possible
future logging layer for autoharn; it is not itself a spec, and nothing in it has been
built yet.

**Provenance:** produced by the commissioned survey analyst (Opus). Legibility repairs
(referent grounding, citation linking, sentence completeness, structure grounding, acronym
expansion) were applied by maintainer-directed A-side pre-review on 2026-07-27; no factual
claim, witness-class marking, number, or the §0 compliance statement's substance was
altered. The as-delivered original is preserved at the filing commit
(`8182f711777504208679b1ef50d75f759fcf2dae`). Its §3 is direction, not design; nothing in it is a spec.
The three upstream defects its §1 found are in the PROXY repository (the maintainer's
other project) and are reported here only — nothing was fixed there (read-only fence).

---

# Survey: `/home/bork/w/omega/proxy` logging → a suggested direction for autoharn

---

## §0 The license fence

**DOC-SOURCED (this report's evidentiary tags, defined once here: DOC-SOURCED = taken
from the cited document's own text, not independently executed; WITNESSED = the surveyor
ran the command or probe and shows the observed output; UNEXERCISED = deliberately not
run, with the concrete blocker or choice stated) — `/home/bork/w/omega/proxy/NOTICE`,
read in full as my first file in that tree, before any other read.** Its operative
terms, verbatim:

> ```
> Project root and all subdirectories EXCEPT `goboard_transposition/`
> ------------------------------------------------------------------------
>
> Released into the public domain under the Unlicense.
> See the file `UNLICENSE` at the project root for the full text.
> ```

> ```
> The `goboard_transposition/` subdirectory
> ------------------------------------------------------------------------
>
> Derived from KataGo, which is distributed under the MIT License.
> ```

and, for the vendored dependency inside it:

> `goboard_transposition/third_party/nlohmann/json.hpp` is the single-header amalgamation of the nlohmann/json C++ library (version 3.11.3), distributed under the MIT License.

**Excluded, and NOT opened by me:** the entire `goboard_transposition/` subtree — including `goboard_transposition/LICENSE`, `goboard_transposition/third_party/nlohmann/json.hpp`, `.../LICENSE.MIT`, and `.../third_party/README.md`. I did not read, grep, glob, or summarize anything under that path. My only enumeration commands carried an explicit `-path ./goboard_transposition -prune` or a `grep -v goboard_transposition` filter; the directory name appears in my transcript only as an exclusion argument.

**Boundary scope is unambiguous** — the NOTICE draws it by directory, not by file, and names `logging_config.py` explicitly in the Unlicense list. Nothing was skipped-as-ambiguous. One adjacent note: `transformers/transposition_enricher.py` sits at the permitted side of the fence (it is in `transformers/`, and the NOTICE names a root-level `transposition_enricher.py` as Unlicense); I opened it only via grep for logger call sites, and it carries no MIT-derived material — it is a proxy-side consumer of the module, not the module.

**Compliance statement.** Files I opened in that tree: `NOTICE`, `docs/logging.md`, `docs/logging-design.md`, `logging_config.py`, all seven files of `proxy_logging/`, `CLAUDE.md` (§ logging conventions), header regions of `proxy_server.py`, the header of `tests/diagnose_log_format.py`, and grep-level (not full-read) access to `router.py`, `pubsub_hub.py`, `middleware/*`, `transformers/*`, `tests/*`. All are on the Unlicense side. Per the commission I quote **no code** from that project; identifier and env-var names only.

---

## §1 The proxy's logging architecture

**Every file path in this section is inside the proxy repository (`/home/bork/w/omega/proxy`), not autoharn**, unless a citation says otherwise; none of these paths resolve inside this repository.

The proxy's logging documentation is split deliberately into two documents. `docs/logging-design.md` (893 lines) is the architectural memo — schema invariants, event vocabulary rationale, phasing, and a recorded decision ledger (Q1–Q6, each with a "Decided:" line). `docs/logging.md` (439 lines) is the operator runtime reference — env-var matrix, formatter shapes, six worked "operator recipes." Each cross-links the other and states which view it is. The proxy's own `CLAUDE.md` (a different file from this repository's `CLAUDE.md`), §"Logging conventions (load-bearing for the structured envelope)" (lines 262–371), is the third leg: standing law for anyone authoring or migrating a call site. *(DOC-SOURCED, those files.)*

The implementation itself is one package of seven modules, 1928 lines total. *(WITNESSED — `wc -l proxy_logging/*.py`.)* `enums.py` (Role, Direction, `LogContractError`), `events.py` (the closed `Event` enum + `EVENT_REQUIRED_FIELDS`), `adapter.py` (`ProxyLogger`), `formatters.py` (three renderers + filters + the env dispatcher), `lifecycle.py` (call-site helpers), `summarize.py` (`log_safe`/`filter_dict`/`summarize_query`), `__init__.py` (public surface). The pre-existing `logging_config.py` was reduced to a 55-line back-compat shim re-exporting `get_logger`/`log_safe`/`filter_dict` — that shim is explicitly what made a file-by-file sweep possible instead of a flag-day rewrite *(DOC-SOURCED, `logging_config.py:1-26` and design memo §11 Phase 1)*.

**The layering, bottom to top:**

1. **A closed event vocabulary.** `Event` is a `str`-valued enum, 44 members across eleven groups plus one `DIAGNOSTIC` catch-all *(DOC-SOURCED, `proxy_logging/events.py:57-137`)*. Adding one is a code change by construction.
2. **A per-event required-field contract.** `EVENT_REQUIRED_FIELDS: dict[Event, frozenset[str]]` is the runtime source of truth; sibling `TypedDict`s carry the full shape as documentation only. The two-declaration split is an acknowledged 3.10 compromise (PEP 655 `Required` needs 3.11+), named as such with its mitigation *(DOC-SOURCED, `events.py:10-24`, `:153-224`, `:227-245`, and design memo §12 "Note on enforcement mechanism")*.
3. **A validating adapter with a bind chain.** `ProxyLogger.bind(**fields)` returns a *new* adapter merging parent context with the supplied fields; call sites never re-supply bound fields. `.log()` runs a fixed four-step order: reserved-name collision check → event recognition → level filter → required-field validation and dispatch *(DOC-SOURCED, `adapter.py:84-206`)*. Steps 1 and 2 run **before** the level filter, deliberately.
4. **Process-wide role.** `set_process_role()` stores a module-global consumed by `get_proxy_logger()`, so every module-level logger carries `role=` without per-module boilerplate; one call site, `proxy_server._main` *(DOC-SOURCED, `adapter.py:297-343`; `proxy_server.py:1327-1333`)*.
5. **Three renderers over one record.** `ConsoleFormatter` (compact, ANSI-tinted per role, ids abbreviated to 6 chars), `LogfmtFormatter` (stable field order: a fixed 13-key header tier then alphabetical tail), `JsonFormatter` (one object per line, full-precision ISO-8601 ts) *(DOC-SOURCED, `formatters.py:50-333`)*. Switching renderers never loses information going up the precision ladder; the console renderer is explicitly lossy and says so.
6. **Two handler-level filters.** `TraceCidFilter` (drop records whose `cid` is present and ≠ target; **no-cid records pass through** so session lifecycle stays visible) and `RegexLineFilter` (free-text grep on the rendered `msg`) *(DOC-SOURCED, `formatters.py:340-380`)*.
7. **Lifecycle helpers.** ~20 thin wrappers pinning the event + default `msg` + field order per common emission. The stated threshold for adding one is "more than two call sites would emit this event with the same default shape" *(DOC-SOURCED, `lifecycle.py`; `CLAUDE.md:294-310`)*.

**How debug logging is enabled/configured — entirely by environment, read once at startup.** `configure_logging_from_env()` is idempotent, installs exactly one handler on the `kataproxy` root logger, and sets `propagate = False` *(DOC-SOURCED, `formatters.py:390-448`)*. The surface: `PYTHONLOGLEVEL` (level), `PROXY_LOG_FORMAT` (`auto|console|logfmt|json`; `auto` = console if stderr is a TTY else logfmt), `PROXY_LOG_DEST` (`stderr|file:<path>`), `PROXY_LOG_TRACE_CID`, `PROXY_LOG_FILTER`, `PROXY_LOG_NO_ABBREV`, `PROXY_LOG_TRUNCATE`, `PROXY_ROLE`. An unrecognized format value raises rather than falling back *(DOC-SOURCED, `formatters.py:424-428`, `:483-486`; `docs/logging.md` §1 table)*.

**Per-request context is a two-level correlation id.** `cid` is the hub's canonical id (post-coalescing); `orig` is the per-subscriber wire id. Two clients coalesced onto one query share a `cid` and differ in `orig` *(DOC-SOURCED, `docs/logging.md` §4.1)*. Context reaches records by bind chain, not by call-site repetition: process role → per-`ClientSession` `session=peer` → per-upstream `upstream=`/`label=` *(DOC-SOURCED, `router.py:391/1133/1205/1710/1911/2513`, `proxy_server.py:1147-1149`)*.

**PII / payload tiering.** INFO carries structural metadata only; DEBUG carries payloads through `filter_dict` (strips `moveInfos`/`ownership`/`policy`); `log_safe` repr-truncates every wire-derived value at `PROXY_LOG_TRUNCATE` chars, which is simultaneously the log-injection defence — `repr()` escapes newlines so a client cannot forge log lines *(DOC-SOURCED, `summarize.py:50-93`; design memo §9)*.

**Rotation is explicitly out of scope** — deferred to stdlib `RotatingFileHandler` and operator-side shipping. So are metrics, distributed tracing, and cross-process correlation *(DOC-SOURCED, design memo §13 and §12 Q4)*.

**Verification.** Per-role *coverage contracts* — each role declares the events it MUST emit during a normal lifecycle, asserted by pytest driving the role through a representative scenario against a `MemoryHandler` *(DOC-SOURCED, design memo §5 and §12 Q3; `tests/test_role_coverage.py` exists at 600+ lines)*.

**WITNESSED — I ran the print-only format matrix** (`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tests/diagnose_log_format.py`, stdout only, no file writes, no live process touched). It rendered all three formatters across all five roles, plus both filters. Observed, among others:

```
15:23:03.724 DEBUG [LEAF] forward cid=hub_ac… orig=wd-177…  ← partial
15:23:03.724 INFO  [LEAF] forward cid=hub_ac… orig=wd-177…  ← final
```

— the kind-aware level split working as documented; and the trace-cid filter keeping the matching `cid` **plus** the no-cid `connect` record, exactly as specified.

### Three defects found in passing (flagged, not fixed — read-only, and not my repo)

**(a) The `module` field is constant and wrong.** *(WITNESSED.)* Across all 31 records the diagnose run emitted, `grep -o 'module=[a-z_]*' | sort | uniq -c` returns exactly one bucket: `31 module=adapter`. The JSON renderer agrees (`"module":"adapter"` on every line). But `module` is one of the six **always-present** fields the schema tells aggregators to rely on, defined as "Python module emitting the record" *(DOC-SOURCED, design memo §3)*, and both docs show it as `module=proxy_server` / `module=router` in their examples *(DOC-SOURCED, `docs/logging.md:111`, `:123`; design memo §6.2)*. Root cause: `ProxyLogger.log()` calls the stdlib logger from inside `adapter.py` without passing `stacklevel=`, so stdlib's caller attribution stops at the adapter frame. The correct information is present on the record as `record.name` (`kataproxy.<module>`), but the formatters' skip-list drops `name` before rendering *(DOC-SOURCED, `formatters.py:130-140`)*. This is a lying field in a schema whose whole selling point is that operators can trust its fields — worth an upstream note.

**(b) `PROXY_LOG_FULL_PAYLOAD` is documented but not implemented.** *(WITNESSED — `grep -rn PROXY_LOG_FULL_PAYLOAD`: seven hits, every one prose.)* The design memo makes it load-bearing in requirement R5, lists it in the §8 env matrix, and names it as the third PII tier in §9; `proxy_logging/__init__.py:52` claims `configure_logging_from_env()` reads it; `summarize.py:175` states the override is "enforced by the formatter, not here." No code reads it. To the project's credit the *operator-facing* `docs/logging.md` §1 table correctly omits it — so the operator surface is honest and the design memo plus the package docstring are stale. Class: a privacy control that exists only on paper.

**(c) `PROXY_LOG_DEST=both` is an accepted no-op aliased to stderr** *(DOC-SOURCED, `formatters.py:475-482`)*. `docs/logging.md` discloses this; the design memo §8 still lists it as a real destination.

---

## §2 What "mature" actually consists of here

Nine properties follow, in rough order of what I'd want in autoharn:

1. **The log is a contract, not output.** A closed event set plus per-event required fields, enforced at the call site with a dedicated exception type. This is the load-bearing idea; everything else is ergonomics around it. The motivating framing in the memo is worth quoting for its posture: *"renaming an event field after operators are parsing it is expensive"* — so schema decisions were made in a reviewable memo **before** any code landed.
2. **Refusals that teach.** `LogContractError`'s message names the event, the full required set, what was missing, and what *was* provided *(DOC-SOURCED, `adapter.py:290-294`)*. Directly the autoharn house shape.
3. **Validation ordering as a safety property.** The reserved-name check runs before the level filter, *because* the `orchestration_spawn` bug shipped a collision that passed at INFO and raised only at DEBUG-filtered call sites — a latent crash armed by an operator turning DEBUG on during an incident *(DOC-SOURCED, `adapter.py:149-162`; `CLAUDE.md:312-338`)*. Generalizable: any validation whose *result* depends on the level filter is a trap.
4. **Bind chains instead of call-site repetition.** Context attaches once, at the object that owns the scope. The convention is stated as law, with the smell named: a call site re-supplying a bound field means either the chain didn't reach it or there's genuine fan-in *(DOC-SOURCED, `CLAUDE.md:340-359`)*.
5. **Two-level correlation ids with a context-preserving trace filter.** "Trace this one unit of work, *plus* the lifecycle around it" is a better primitive than strict id filtering, and the memo says why.
6. **One record, N renderings, switchable without redeploy semantics.** Also: an unrecognized format value *refuses* rather than silently falling back.
7. **Coverage-contract tests.** The log is treated as a deliverable with an assertable obligation per role. When a new code path should emit a contract event, a test fails until the call site exists.
8. **One repr-truncating chokepoint for every wire-derived value**, serving double duty as PII bound and log-injection defence.
9. **A design memo carrying its own decision ledger** (Q1–Q6, each answered on the record) and a phased migration where each phase leaves the tree buildable.

### Worth NOT adopting for autoharn's shape (stated honestly)

Seven specific things the proxy does well for its own shape but that autoharn should not copy, each with why:

- **The lazy import.** `lifecycle.py:227` does `import logging as _logging` inside `forward()`; `proxy_server.py:1327` defers the whole `proxy_logging` import inside `_main`. autoharn bans these outright, mechanically (`gates/no_lazy_imports.py`). Don't carry the pattern across with the ideas.
- **The scale.** 1928 lines and 44 events is right for a five-role async proxy emitting per-partial-response records at DEBUG. autoharn's serving layer is 14 routes and one write path. Starting at proxy scale would be work ahead of demonstrated need ([ADR-0003](../law/adr/0003-domain-coupling-bands.md)'s "explicit seams without premature extraction" — this survey's original citation named ADR-0004, which is about a different discipline (minimal-touch edits); retargeted to the ADR that actually states this principle). ~8 events is the honest analogue.
- **Three formatters.** The proxy's console renderer earns its keep because operators watch three interleaved proxy processes on one terminal. autoharn's boundary service is a detached child whose output already goes to a file. One machine-readable rendering plus the existing human stderr lines is likely enough; a second renderer is cheap to add later and a surface to keep honest now.
- **Env vars as *the* config channel.** Correct for the proxy (env is how it's launched). autoharn's boundary service already takes `--config <toml>` with a whole-file validation pass before the socket binds; a parallel env namespace would be a second config channel for the same process.
- **Two sources of truth for the field schema.** The proxy names this compromise honestly and pins both in tests, but it exists only because it targets 3.10. autoharn's serving venv is 3.13 (the `__pycache__` entries are `cpython-313`), so one declaration suffices — don't inherit a workaround for a constraint that doesn't apply.
- **Deferring cross-process correlation (memo Q4).** Right for the proxy — the cid is its tracer. Wrong for autoharn: *session identity is exactly the gap the row-1474/1476 attribution
incident named* (the two unattributed refused writes §3.4 details). This is the one place where the direction should diverge from the source rather than copy it.
- **The `module` defect (a) above.** Whatever autoharn builds on top of stdlib `logging` must pass `stacklevel=` or render the logger name — otherwise it inherits a field that lies.

---

## §3 Suggested direction for autoharn

### 3.0 First: the named-consumer test, applied before anything is proposed

Three readers, each with a decision:

- **RCA of an unattributed write** — the maintainer, or an agent attempting the same
  reconstruction. Ledger rows 1474 and 1476 are two `write_refused` rows logged at 14:11
  with no session or command recorded; row 1483 later traced their probable cause, but
  only by manual interrogation the record itself did not support. Decision: *which
  session and which command produced this attempt?*
- **An operator facing a refusing or slow boundary.** Decision: *is this saturation, a stall, or a dead world — restart the service, or look at the world?* The service already computes these as distinct typed dispositions; today they are indistinguishable after the fact.
- **The identity-plumbing build (ledger row 1471, the maintainer's decision ratifying that per-request caller identity gets plumbed through the HTTP request).** Decision: *what per-request context object exists to hang a principal stamp on?* Ledger row 1467 (the finding that confirmed served writes carry no per-request stamp) closes with the observation that `_psql()` is the single site where a per-request stamp could thread in *if caller identity were plumbed through the HTTP request*. That plumbing and this logging want the same object.

Any stream that cannot name one of these — or a successor as concrete — doesn't get built.

### 3.1 The line that must not be blurred: diagnostic vs evidentiary

Standing rule: the action stream and the ledger are the **evidentiary** basis; logs would be **diagnostic-grade**, never load-bearing for a guarantee. Two concrete corollaries I'd want stated in any spec:

- **No fact may live only in the log.** If a guarantee rests on it, it goes through s43 (kernel-lineage migration [`s43-typed-verdict-write-boundary.sql`](../kernel/lineage/s43-typed-verdict-write-boundary.sql), which added the refusal journal cited just below) into the ledger.
- **This direction does not close the rows-1474/1476 attribution gap by itself, and should not be sold as doing so.** That gap is *kernel-side*: the s43 refusal journal licenses exactly six `refusal_*` columns — sqlstate, message, surface, payload_digest, attempted_actor, attempted_role *(DOC-SOURCED, [`kernel/lineage/s43-typed-verdict-write-boundary.sql:425-431`](../kernel/lineage/s43-typed-verdict-write-boundary.sql))* — and carries no session identity, because served writes are unstamped (row 1467's second consequence). Logs would have made that RCA *faster*; only the journal can make it *sound*. So: **two work items, not one.** The evidentiary one (row 1471's identity plumbing) is the real fix. The diagnostic one below is cheap, can land first, and must not become the excuse to defer the other.

### 3.2 What it would join on

The valuable thing a request log can do without becoming evidence is supply a **breadcrumb that joins to the ledger**. Every served write already yields either a kernel verdict with a row id, or a journaled `write_refused` row carrying `refusal_id` and `refusal_payload_digest`. If the request record carries `(request_id, route, deployment, caller identity once plumbed, payload digest, verdict, refusal_id)`, then a `write_refused` row becomes joinable back to the request that caused it — the ledger stays the sole authority, the log supplies provenance.

**Caveat, to be witnessed rather than assumed:** the digest is computed kernel-side over whatever bytes the boundary function received. For the join to be sound, the service must digest *the same bytes*. Whether the service's re-serialized payload (`json.dumps(..., allow_nan=False)`, per [`design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md`](FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md) §A4.1) is byte-identical to what the kernel digests is an open question that needs a scratch-world witness, not a design assertion.

### 3.3 Layers

**L1 — one per-request context object.** A single FastAPI dependency or middleware mints a request id and records deployment, route, method, client address, and (once row 1471's work lands) the declared principal/session. Held in a `contextvars.ContextVar`. This is the proxy's bind chain specialized to one request scope, and it is the object the identity work needs anyway — build it once. **Needs a witness, not an assumption:** the write handlers are plain `def` dispatched to Starlette's threadpool (per [`design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md`](FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md) §A3.1); contextvars *do* propagate through `run_in_threadpool`, but that should be proven live on this stack before anything depends on it.

**L2 — a small closed event vocabulary with per-event required fields.** Candidate starting set, each with a reader from §3.0: `request_start` / `request_end` (route, deployment, status, duration_ms), `kernel_call` (surface, psql exit code, duration), `refusal` (the typed disposition), `write_verdict` (accepted|refused, row id or `refusal_id`, payload digest), `infra_failure`, `unclassified_failure`. Eight, not forty-four. Validated at the call site against a required-field frozenset, raising a dedicated error whose message teaches — the proxy's `LogContractError` message shape is directly copyable, and it is [ADR-0002](../law/adr/0002-fail-loudly.md)'s (fail loudly) rung applied to the log's own contract.

**Generic mechanism, not a parallel enumeration:** the refusal events should be **derived from** the dispositions the service already computes (`payload_too_large`, `body_read_timeout`, `unknown_view`, `unknown_deployment`, `server_saturated`, `deployment_saturated`, `capability_absent`, the value/representability/id-domain axes, `infra_failure`, `unclassified_failure`), not maintained beside them. One enumeration, so a future amendment in the boundary spec's A-series (the dated Amendment A2/A3/A4/A5 numbering [`serving/README.md`](../serving/README.md) carries — the A3.1/A4.1 codes cited above are its sub-items) adding a disposition gets its log event by construction rather than by a second edit someone forgets.

**L3 — one rendering: JSON lines.** The served process's output already goes to a file, not a terminal. Console prettiness is not the need. Keep the existing human `sys.stderr.write` lines as-is alongside it.

**L4 — migrate the existing sites.** `_log_infra_failure`, `_log_unclassified_failure`, and the startup banner *(DOC-SOURCED, [`serving/boundary_service.py:1262-1272`](../serving/boundary_service.py), `:2430-2450`)* are already the right *content* — loud, server-side-only, never client-exposed. They are just untyped and unjoinable. They become the first four call sites, not a separate stream.

**Config surface:** put level/format in the existing multiplex TOML that already validates whole-file before the socket binds, rather than a new env namespace. Leave the destination alone — [`serving/ensure_running.py:160`](../serving/ensure_running.py) already sends the detached child's stdout+stderr to `<world>/service.log`, and nothing about deployment should change.

**This direction respects the following standing rules:** no lazy imports (every import top-of-file — the proxy's own two violations are the counter-example); fail loudly (an unknown event or missing field raises, it does not emit a malformed record); refusals that teach; diagnostic-only, per §3.1.

### 3.4 The maintainer's literal question: is there debug logging to just enable?

**Partly — and less than it looks.**

1. **There is no autoharn-authored logging layer to turn up.** *(WITNESSED — `grep -rn "import logging" --include='*.py'` across the repo returns two hits, both in `tools/makespan-scheduler/`.)* Nothing in `serving/`, `filing/`, `hooks/`, or the operator verbs imports `logging`; every diagnostic is a direct `sys.stderr.write`. So there is no level to raise.

2. **But uvicorn's own default logging is already on and already captured.** `uvicorn.Config(app, host=..., port=...)` is constructed with no `log_config` or `log_level` *(DOC-SOURCED, [`serving/boundary_service.py:2592`](../serving/boundary_service.py), `:2594`)*, so uvicorn's defaults apply, and [`serving/ensure_running.py:224-231`](../serving/ensure_running.py) redirects the detached child's stdout+stderr into `<world>/service.log`. **WITNESSED:** `/home/bork/w/vdc/1/autoharn/service.log` (a gitignored, host-local runtime artifact -- `.gitignore:53`, `/service.log` -- absent from a fresh checkout by construction, so not a live link target here) is 1410 lines, including the startup banner, three server-process lifecycles, one `WARNING: Invalid HTTP request received.`, and 223 `POST /d/autoharn2/write/ledger` access lines. My own `./autoharn led show 1474/1476/1483/1467/1471` reads for this survey appear in it.

3. **What it buys today, honestly: not the incident.** **WITNESSED:** `grep -cE '[0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{2}:[0-9]{2}:[0-9]{2}'` over that file returns **0** — uvicorn's default access format carries no timestamp at all. And a kernel-refused write is HTTP 200 by design (a refusal is a first-class domain result, not a transport error). So the two 14:11 refusals of rows 1474/1476 *are* in that file, wearing `200 OK`, indistinguishable from the other 221 writes, with no time, no body, no principal, and only an ephemeral loopback source port as a discriminator. **Enabling nothing further, this log could not have attributed those rows.**

4. **The one genuinely free win — timestamps on the access log.** Passing a `log_config` to `uvicorn.Config` that adds an ISO-8601 timestamp to the `uvicorn.access` and `uvicorn.error` formatters is roughly fifteen lines, no new dependency, no new concept, no change to how the service is operated. It would have narrowed the incident from "one of 223 POSTs" to "the two POSTs at 14:11:01" — which, against the ledger's own row timestamps, is a real correlation the operator did not have. **The format change is safe:** `service.log` (gitignored, host-local, not a link target -- see the note above) is only ever *pointed at* for a human to read, never parsed *(WITNESSED — `grep -rn "service\.log"` finds five references, all of them prose telling an operator where to look: [`bootstrap/templates/doctor.tmpl:259`](../bootstrap/templates/doctor.tmpl), [`user-guide/USER-GUIDE.md:112`](../user-guide/USER-GUIDE.md), [`bootstrap/new-project.sh`](../bootstrap/new-project.sh)`:348/2086`, [`serving/ensure_running.py:160`](../serving/ensure_running.py))*. I'd take this step regardless of whether the larger build ever happens.

5. **psql verbosity: I'd not turn it up as a standing setting.** `_psql` already captures stderr, and the infra/unclassified paths already log its last 2000 chars server-side *(DOC-SOURCED, [`serving/boundary_service.py:1009-1016`](../serving/boundary_service.py), `:1262-1272`)*. A global libpq verbosity increase would put SQL text into a file guarded only by filesystem permissions, against a service that deliberately keeps SQL off every client-visible surface. If more psql detail is wanted, the honest place is those two existing chokepoints.

6. **Hook stderr: nothing to enable, and the wrong place to start.** Fifteen of the seventeen hooks already write to stderr, which Claude Code surfaces; the only hook env vars are two timeouts (`DOC_CRITIC_TIMEOUT_S`, `DEMURRAL_TIMEOUT_S`), not verbosity controls. And the standing rule forbids touching `hooks/` while a live session runs there.

---

## §4 Closure

**Surveyed.** The proxy's entire Unlicense-side logging surface (all paths below are inside the proxy repository, not autoharn): both design and operator documents in full, all seven `proxy_logging` modules in full, the compatibility shim, the proxy's own `CLAUDE.md` conventions section, the call-site wiring in `proxy_server.py`/`router.py`, and the full call-site census by grep. One read-only execution witness (the format-matrix diagnose script). On the autoharn side: [`serving/README.md`](../serving/README.md) in full, the [`serving/boundary_service.py`](../serving/boundary_service.py) header and its `_psql`/exit-classification region, [`serving/ensure_running.py`](../serving/ensure_running.py)'s spawn and log-redirect path, the s43 refusal-journal column set (see [`kernel/lineage/s43-typed-verdict-write-boundary.sql`](../kernel/lineage/s43-typed-verdict-write-boundary.sql) above), ledger rows 1474/1476/1483/1467/1471 (glossed at first use in §3.0), and the live `service.log` (gitignored, host-local, not a link target -- see §3.4 item 2's note).

**Excluded by the fence.** The whole `goboard_transposition/` subtree, unopened. Nothing skipped-as-ambiguous.

**Boundaries honored.** Read-only in both repositories; no file writes anywhere (the one script I ran prints to stdout and was run with `PYTHONDONTWRITEBYTECODE=1`); ledger reads via `./autoharn led show` only; no ledger writes; ports 8433/8422 and every live process untouched; nothing under `~/.claude`; no proxy code copied into this report.

**Open, and left open deliberately.**

- Whether the service's re-serialized payload digests identically to the kernel's `refusal_payload_digest` — the join in §3.2 depends on it, and it needs a scratch-world witness. **UNEXERCISED** (would require a live write, outside this commission's read-only boundary).
- Whether contextvars survive Starlette's `run_in_threadpool` on this stack's exact versions. **UNEXERCISED**, same reason.
- The proxy's `module`-field defect, the unimplemented `PROXY_LOG_FULL_PAYLOAD`, and the `both`-alias no-op: found and flagged here, not reported upstream — that's the maintainer's call, and it's a different repository.
- No design authority claimed. Everything in §3 is a direction for the maintainer and coordinator to accept, cut, or reject; nothing here is a spec.
