<!-- doc-attest-exempt: the +A:B:C loop RAN and closed on this suite 2026-07-28 (A-side
pre-review + three blind suite-wide rounds, DEFECT trend 11-6-2, every DEFECT repaired,
coordinator adjudication on the record at ledger row 313; per-file doc-attestation/2
records with the full round history are appended to the attestations jsonl the same
day). This waiver marker persists ONLY because the record schema's own two-round cap
(gates/doc_attestation_presence.py refuses rounds>2 and umbrella verdicts) cannot yet
represent a three-round adjudicated loop -- filed as work item
attestation-schema-multiround; strike this marker when the schema can carry the loop
that actually ran. -->

# CLI and boundary — recipes

*Factored out of [`user-guide/USER-RECIPES-FAQ.md`](../USER-RECIPES-FAQ.md) at commit
`178ec789439044bebb664e7374c2be757d064d11`, sections "The ledger boundary service (`serving/`)", "Reaching the ledger through a
shared boundary service, and compiling workflow units (2026-07-18)", "CLI quality-of-life:
row-id echo and `judge` auto-layer detection", and "`led` help tokens, `--json` payload mode,
and `work list`'s default filter (led.tmpl trio)"; byte-preserving (mechanical `../` depth
repairs and named cross-file link rewrites only). One residue named at the split was SINCE FIXED (suite legibility loop, blind round 1) -- per this
work item's execution report: a pre-existing wrong-direction pointer ("... section below"
where the target is actually earlier in this same file) is now corrected in place with an inline editorial note,
same as it stood in the original page.*

**Charter:** the verbs and the service that carries them. Belongs: endpoint shapes, exit codes,
flags, defaults, multiplexing, the workflow-unit compiler, `led` ergonomics. Does not belong:
what the kernel decides once a call arrives (see IDENTITY-AND-AUTHORITY.md / EVIDENCE-AND-TRUST.md
/ THE-RECORD.md in this directory).

---

## The ledger boundary service (`serving/`)

**Can I get an HTTP API onto a ledger instead of shelling out to `led`?**
Yes — `serving/boundary_service.py` is a FastAPI service that is the one declared **Port**
([ADR-0012](../../law/adr/0012-compositional-and-structural-hygiene.md) P2) into an autoharn-managed ledger for UI-class and programmatic consumers, the
autoharn-panel Vue SPA first. Full spec:
[FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md](../../design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md) (read it in full,
including its amendments, before touching the directory); operator pointer:
[serving/README.md](../../serving/README.md). The service adds **no truth of its own** — it
translates and validates transport-level shape only, refuses what it cannot honor, and never
coerces. The kernel's own **inner** boundary (the [write boundary](../../GLOSSARY.md#write-boundary)
s43's four `SECURITY DEFINER` functions, plus the derived views) stays the sole authority.

**UPDATED 2026-07-18 — the repo-root operator verbs are no longer a separate, un-served
surface.** The paragraph above once said `led`/`judge`/`pickup` were "explicitly NOT
deprecated by this — routing them through the service is a reserved v2 question." That v2
question is now answered and built: `led`, `pickup`, `asof-export`, and `distance-to-clean`
became thin HTTP clients of this service (the ["Reaching the ledger through a shared boundary service, and compiling workflow
units (2026-07-18)"](#reaching-the-ledger-through-a-shared-boundary-service-and-compiling-workflow-units-2026-07-18)
section below -- pre-split working title "boundary multiplex and CLI rebase, and the
workflow-unit compiler" -- has the full story, including the two new
`deployment.json` keys this rebase needs and what happens when they're missing). `judge` and
`audit` do **not** rebase — they drive `clingo` plus a differential against the world directly,
"not a ledger client in the boundary's sense" (the rebase spec's own words) — and neither does
the scaffolding itself.

**How do I launch it, and what does it actually say?** The service used to take a single
`--deployment deployment.json` file; **as of the 2026-07-18 multiplex build it takes
`--config <path-to-boundary-multiplex.toml>` instead** and can serve more than one deployment
from one process (see "How do I serve more than one project from one boundary?" below for the
config shape and the `/d/{deployment}` routing this changes). The single-file `--deployment`
launch form below is UNWITNESSED against the current build — retained here as history of what
this section originally verified, not as a current invocation to copy:
```
$HOME/w/vdc/venvs/generic/bin/python -m serving.boundary_service --deployment deployment.json --port 18421
```
(the example above ran on port 18421 rather than the default 8420 because another project's dev
server already held 8420 on this host — an ordinary `--port` override, not part of the feature).
WITNESSED, `GET /health` against this repo's own `autoharn1` world:
```
{"world":"autoharn1","service_principal":null,"capabilities":{"s22_work":true,"s41_identity":false,"s43_boundary":false,"credited_view":false}}
```
That capability manifest is not a fixed feature list — it is DETECTED per request against the
connected world's actual schema (object existence, never a version literal), which is why
`autoharn1` — a world older than s40/s41/s43 — shows three of the four capabilities absent
while still serving [`s22`](../../kernel/lineage/s22-work-item-ledger.sql) (the kernel-lineage
delta that adds the per-project work-item ledger) work items fine.

**What do the read endpoints look like, and what happens when a world lacks a capability
a read endpoint needs?**
`GET /rows/current` serves `ledger_current` (id-paginated, `?after_id=&limit=`, `1 ≤ limit ≤
1000`, `after_id ≥ 0`); `GET /rows/{id}` and `GET /rows/{id}/history` serve one row and its
supersession chain. `GET /credited`, `GET /standing/principals`, and `GET /work/items` are
**capability-gated** — on a world that lacks the underlying view, the endpoint refuses with a
typed `capability_absent` response rather than silently falling back to a weaker read (that
fallback is exactly the vacuous-pass class this project's [F49 finding](../../FINDINGS.md) named:
a close instrument that silently no-ops instead of visibly refusing when its assumed
environment isn't met, so the missing check reads as a pass). WITNESSED, all
three gates against `autoharn1` (which lacks s41 identity and the s44 credited view, but carries
s22 work):
```
GET /credited            -> HTTP 409 {"disposition":"capability_absent","capability":"s44-credited-view", ...}
GET /standing/principals -> HTTP 409 {"disposition":"capability_absent","capability":"s40-identity", ...}
GET /work/items          -> 200, real work_item_current rows
```

**What does a write look like, and what happens to a refused one?**
Four endpoints, one per s43 [write boundary](../../GLOSSARY.md#write-boundary) function:
`POST /write/ledger`, `/write/review`, `/write/registration`, `/write/obligation`. **A kernel
refusal is HTTP 200** carrying the kernel's own [typed verdict](../../GLOSSARY.md#typed-verdict)
verbatim (`disposition: "refused"`, `refusal_id`, `sqlstate`, kernel-authored teach-text) — a
refusal is a first-class domain result, not a transport error. Transport-level failures
(malformed JSON, an oversized body) are typed and loud instead: a body over 1 MiB is HTTP 413
with `{"disposition":"payload_too_large", ...}`, checked before JSON parsing and again before
the value reaches the database. **On a world that predates s43, every write endpoint refuses
entirely** rather than falling back to a raw `INSERT` — there is no code path in the service
that writes SQL DML. WITNESSED against `autoharn1` (pre-s43):
```
POST /write/ledger -> HTTP 409 {"disposition":"capability_absent","capability":"s43-boundary",
  "message":"This world carries no s43 write boundary ... refuses entirely rather than
  falling back to a raw INSERT ..."}
```
The 413 oversized-body and malformed-JSON write-path checks are **UNWITNESSED here** — on
`autoharn1` the s43 capability gate short-circuits before those checks run at all, since the
world has no write boundary to reach; they would need an s43-carrying world to observe.

**Does it bind to the network, or only to this machine?**
Loopback only by default (`127.0.0.1:8420`); any other host is refused at startup unless you
pass `--i-understand-this-exposes-the-ledger` — the ledger carries operator-real content.
WITNESSED:
```
$ python -m serving.boundary_service --deployment deployment.json --host 0.0.0.0 --port 18422
boundary_service: REFUSED -- --host '0.0.0.0' is not a loopback address ... refused unless
you pass --i-understand-this-exposes-the-ledger explicitly ...
```

**Is there a way to check the service is actually telling the truth about what the kernel
holds?** Yes — `serving/audit_served.py` fetches a served page over HTTP, reads the same view
directly with a read-only `psql`, and byte-compares the row sets; it ships WITH the service —
sentry-class treatment, this page's term for a built-in independent verifier shipped alongside
the primary tool rather than bolted on afterward, the same posture the OTel watchdog/sentry
mechanism in ["Model identity: watchdog, attestation, defeat"](EVIDENCE-AND-TRUST.md#model-identity-watchdog-attestation-defeat) (in the evidence-and-trust recipes) uses for a different
surface — not as an afterthought. WITNESSED:
```
$ python serving/audit_served.py --base-url http://127.0.0.1:18421 --deployment deployment.json
audit_served: AGREE -- /rows/current matches autoharn1.ledger_current byte-for-byte over the
compared page.
```

**What about the panel's existing direct-psql access — does this retire it?**
That is the deprecation duty the spec's §6 names: every legacy direct-psql consumer path (the
autoharn-panel's own FastAPI-side SQL, concretely) gets a mark that is loud at every invocation,
names the replacement endpoint, and points at the world-context migration consult — but stays
functional (backwards compatibility is the commission's own carve-out; nothing is silently
tolerated, nothing is silently broken). That marking is panel-repo work, out of scope for this
autoharn checkout and UNEXERCISED from here — the spec is explicit that the panel-side session
runs it, citing this spec, never a session running against a live panel checkout from here.

## Reaching the ledger through a shared boundary service, and compiling workflow units (2026-07-18)

The four recipes below cover the same day's landed work: the operator verbs `led`/`pickup`/
`asof-export`/`distance-to-clean` became HTTP clients of the boundary service above rather than
direct `psql` callers, the service itself learned to serve more than one deployment from one
process, and a new compiler turns a fixed-shape workflow TOML into something the kernel actually
drives. Specs: [FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md](../../design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md)
(ratified, ledger row 1631), [FABLE-BOUNDARY-READ-SURFACE-SPEC.md](../../design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md)
(ratified, ledger row 1652 — the amendment that grew the route table from eleven to fourteen so
the CLI rebase had a read surface to land on), and
[FABLE-WORKFLOW-UNIT-COMPILER-SPEC.md](../../design/FABLE-WORKFLOW-UNIT-COMPILER-SPEC.md) (commission
ledger row 1658, ratified rows 1659/1660). Operator pointer for the served side:
[serving/README.md](../../serving/README.md).

**My `./led` says the boundary is unreachable, or that `deployment.json` is missing keys — what
do I do?**
As of this rebase, `./led`/`./pickup`/`./asof-export`/`./distance-to-clean` are thin HTTP clients
of the boundary service, not direct `psql` callers — and every rebased shim needs two new
**optional** `deployment.json` keys to find that service: `boundary_url` (the served boundary's
own base URL, no trailing slash, no `/d/{deployment}` segment) and `boundary_deployment` (the
`/d/{name}` path segment this project answers under on the served side — deliberately a
*different* field from `deployment.json`'s pre-existing `name`, so the two don't collide on one
meaning). Read `serving/boundary_cli_client.py`'s own module docstring for the exact shape. Three
distinct failure shapes, and they carry three distinct exit codes so you never mistake one for
another:
- **Exit 4 — boundary unreachable / `deployment.json` missing the two keys.** WITNESSED against a
  `deployment.json` with the two keys deliberately stripped out (a `--profile tracker` deployment,
  the modern standing work tracker, gets both keys automatically now — see below):
  ```
  $ ./autoharn led --recent 3
  led: deployment record at .../deployment.json is missing required-for-the-served-shim
  field(s): boundary_url, boundary_deployment (... refused-if-absent, never guessed. Add both
  keys to .../deployment.json, or run the ./legacy/ original instead.
  ```
  (exit 4). The same exit code covers a genuinely unreachable service (both keys present, but
  nothing is listening at `boundary_url`) — `boundary_cli_client.py`'s own convention: "this shim
  never had a response to classify."
- **Exit 3 — the boundary itself refused** (a typed HTTP 4xx/408/413/422/429/503/409 shape FROM
  the service — `payload_too_large`, `server_saturated`, `deployment_saturated`,
  `unknown_deployment`, `unknown_view`, `capability_absent`, and the like). There was no kernel
  `write_verdict` at all for this call — a boundary-level refusal is never dressed as a kernel
  one.
- **Exit 1 — the kernel itself refused** (a genuine s43 `write_verdict` with
  `disposition: "refused"`) — byte-identical to what the direct-`psql` `led` always exited for
  exactly this case. Exit 0 is the kernel-accepted case, likewise byte-identical to the legacy
  exit.

**`./legacy/` was the recovery path for `pickup`/`asof-export`/`distance-to-clean` — `led` is the
one exception now.** legacy-led-retirement (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md, ledger
row 1149/1150) DELETED `bootstrap/templates/legacy-led.tmpl` outright, once the served path grew
full coverage (below) — `./legacy/led` is now a one-line teaching refusal, never a working CLI.
`./legacy/pickup`/`./legacy/asof-export`/`./legacy/distance-to-clean` are unaffected: demoted by
placement, still executable, unchanged in capability, written automatically by
`bootstrap/new-project.sh --new-world`.

**RESOLVED 2026-07-25 (ledger row 1271) — the standing-tracker `led` gap this retirement once
flagged here as open.** `bootstrap/track-work.sh` (the *other* scaffold) is now a one-line
teaching-refusal stub; its offering lives on as `bootstrap/new-project.sh --profile tracker` (see
[USER-GUIDE.md §3a](../USER-GUIDE.md#3a-just-track-your-work-bootstrapnew-projectsh---profile-tracker)
and
[`TRACK-WORK-RETIREMENT-HERITAGE.md`](../TRACK-WORK-RETIREMENT-HERITAGE.md)), which DOES write
`boundary_url`/`boundary_deployment` (a picked free port + `boundary-multiplex.toml`) — the
service just isn't STARTED at scaffold time. `serving/ensure_running.py`'s
`ensure_running_or_leave_unreachable`, already wired into every served shim, spawns it as a
detached child on this deployment's first `./led`/`./pickup`/etc call, dissolving the "a standing
tracker runs no boundary service by design" rationale that produced the original gap: standing
one up no longer requires an operator action at all, so there is no longer a reason for a
standing tracker to omit the two keys. `./led` works out of the box in this profile.

**How do I serve more than one project from one boundary?**
`serving/boundary_service.py` used to take `--deployment deployment.json` (one process per
deployment); it now takes `--config <path-to-boundary-multiplex.toml>` and serves every
deployment the TOML names from one process — "I don't want to have to start one FastAPI server
for every deployment," the maintainer's own framing for the commission. Shape
(`serving/boundary_multiplex_config.py`'s own module docstring has the authoritative version;
note it needs two more `pg`-prefixed keys than the design spec's own illustrative example, named
there as a flagged, smallest-honest-choice addition):
```toml
[deployments.autoharn1]
pghost = "192.168.122.1"
pgdatabase = "autoharn1"
pguser = "led_writer"
pgschema = "autoharn1"
pgkern = "autoharn1_kernel"

[deployments.omega]
pghost = "192.168.122.1"
pgdatabase = "omega"
pguser = "led_writer"
pgschema = "omega"
pgkern = "omega_kernel"
```
The WHOLE file validates before the socket binds — an unknown key, a missing required key, or
zero deployments all refuse startup by name; per-deployment reachability is *not* probed at
startup (a deployment whose database is down is a per-request typed 503, exactly as before).
Every route in the endpoint table gains a mandatory leading `/d/{deployment}` segment —
`GET /rows/current` is actually `GET /d/{deployment}/rows/current` — and `{deployment}` is valid
iff it's a key of the loaded config; anything else is a typed 404 `unknown_deployment` naming the
known set. This holds even for a config with exactly one deployment (the mandatory discriminator
is one route shape, not two dialects — [serving/README.md](../../serving/README.md)'s own
"Multiplexing" section has the admission-bound details: `MAX_INFLIGHT_KERNEL_CALLS` stays the
global bound, and a new per-deployment sub-bound stops one stalled deployment from starving its
siblings). UNWITNESSED in this pass — launching a live two-deployment multiplexed server was out
of scope for a documentation-only session; `seen-red/boundary-multiplex/run_fixtures.py` — its own
four numbered witness cases WM1 through WM4, covering cross-deployment write isolation, the
unknown-deployment refusal, malformed-config refusal, and per-deployment admission saturation
respectively (the multiplex spec's own §7 names each in full) — is the project's own live witness
suite for this mechanism, cited rather than re-run here.

**Which `led` subcommands go over the boundary?** As of legacy-led-retirement (ledger row
1149/1150), ALL of them — read `bootstrap/templates/led.tmpl`'s own module docstring (its "SCOPE,
HONESTLY NAMED" section) for the authoritative, self-updating coverage table. In brief: `led
--recent`/`current`/`show`; every read view (`question-status`/`review-gap`/`stamp-distinctness`/
`standing`); `led --json`; the generic write path with its full flag set and statement-grammar
pre-flight (all eight prefixes); `register-principal`; `obligate` and `obligate revoke` (a typed
kernel event now, kernel/lineage/s57-obligation-revocation-event.sql — the raw `DELETE` this used
to be is retired); `review`; `decomposition-review-status`; `briefing`; the entire `led work *`
family, all eleven sub-verbs; `led artifact put|get|stat`; and `led principal *`, all thirteen
sub-verbs (`declare-standing`/`undeclare-standing`/`suspend`/`lift-suspension`/`revoke`/`relate`/
`unrelate`/`bind-role`/`release-role`/`bind-key`/`revoke-key`/`grant-competence`/
`withdraw-competence`) — the one family this inventory pass's own mechanical dispatch-diff found
still missing, now closed. `./legacy/led` served none of this specially — it is deleted outright,
a one-line teaching refusal in its place. The two disclosed read-shape divergences named
throughout `led.tmpl`'s own SCOPE section (JSON-per-line listing for `led work list`; the
supersession-aware `led work asof`) are the only remaining behavior differences from the
(now-historical) direct-psql original.

**How do I turn a fixed-shape workflow TOML into something that actually runs?**
`tools/workflow_compile.py` reads one `design/workflows/*.toml` (the pipeline-dsl-v0 grammar —
`[[phases]]` with `name`/`depends_on`, `[roles.<phase>]` with `authors`/`implements`/`reviews`
prose) and emits two artifacts: a **hydration script** (`hydrate.sh` — one `led work open` per
phase, one `led work depends ... blocks-start` per `depends_on` edge, and an obligation act where
a phase's `reviews` clause reads as an independent countersign) and a **driver script**
(`drive.py` — claims each phase, prints its brief for the caller's own agent dispatch, then
closes it). Usage: `python3 tools/workflow_compile.py <path-to.toml> [--out-dir DIR]`, then
`bash <out-dir>/<stem>/hydrate.sh --instance <token> [--yes]` and
`python3 <out-dir>/<stem>/drive.py --instance <token>` — the `--instance` token is **mandatory**
on both (a TOML is a reusable shape; an instance is one engagement of it — slugs are
`<stem>-<instance>-<phase>`, so two different tokens are two independently claimable waves of the
same TOML, and re-hydrating the SAME instance is idempotent by refusal: an already-open slug
refuses loudly and the script treats that as "already hydrated," never as an error).

**The one design commitment that makes this safe to trust: the compiler adds no enforcement
machinery of its own.** Every blocking mechanism the driver obeys is a kernel fact it discovers by
*attempting the act and reading the kernel's own refusal* — never precomputed. A dependency
blocker is the s39 `blocks-start` claim-time refusal; an obligation blocker is countersign debt
visible in `review_gap`; a role constraint is whatever the claiming principal's own standing
permits. WITNESSED, both polarities, compiled from `design/workflows/faq-abc-fixpoint-loop.toml`
and hydrated/driven against a scratch `--new-world` scaffold (`faqwit0718wc` on the toy database,
torn down with zero residue afterward) — claiming a dependent phase before its antecedent closed
(HISTORICAL transcript, captured via `./legacy/led` back when `led work *` ran through it; the
generated driver's own default now runs the served `./led` instead, per legacy-led-retirement,
ledger row 1149/1150 — the kernel-refusal TEXT below is unchanged either way, it is the SAME s43
`write_verdict`):
```
$ ./legacy/led work claim faq-abc-fixpoint-loop-demo2-fresh-context-review
led: REFUSED by the kernel write boundary (SQLSTATE P0001; journaled as write_refused row 24 ...):
  Ledger policy: claim of work item '...fresh-context-review' refused — its blocks-start
  antecedent(s) are not yet resolved: ...author-draft (item is not yet closed). Claim and finish
  each named antecedent first ...
```
and the identical claim accepted once the antecedent was genuinely closed:
```
$ ./legacy/led work claim faq-abc-fixpoint-loop-demo2-fresh-context-review
led: row 31 written.
```
**Suspension halts a wave; lifting it resumes the wave — this is the same kernel-refusal-is-the-
gate posture, not a special case the driver codes for.** Suspend the claiming principal (the s45
standing act) mid-wave and the driver's next claim/write on that principal's behalf is refused by
the kernel with its own teach-text, never simulated by the driver; lift the suspension and the
same act is accepted. The compiler spec names a standing rule for this witness (its own "WC7,"
the seventh named witness case in
[FABLE-WORKFLOW-UNIT-COMPILER-SPEC.md](../../design/FABLE-WORKFLOW-UNIT-COMPILER-SPEC.md)): if any
kernel act the driver relies on turns out NOT to gate on the actor's standing, that must be
reported loudly as a candidate kernel-lineage gap for the maintainer to rule on, never patched
over by having the driver simulate the halt itself. This project's own build witness (ledger row
1661) ran WC7 both polarities and reported **no such gap** — every write gates on the actor's
standing universally, so there was nothing for the driver to route around even by accident.
UNWITNESSED in *this* documentation pass (re-running WC7 was out of scope here) — cited from the
build's own witness record rather than re-driven.

**Named seams, honestly, if you're deciding whether to lean on this compiler for something load-
bearing:** the driver's own phase-count tally undercounts cosmetically (a display bug, not a
correctness one — the kernel's own claim/close verdicts are still what gates everything); the
compiler's own **J2** heuristic (named for its position in `tools/workflow_compile.py`'s own
"JUDGMENT CALLS THIS TOOL MAKES" list — J1 is the principal-identity default, J2 the one named
here, J3/J4 cover obligation-act deduplication and close-disposition defaults) that decides "does
this phase's `reviews` clause want an independent obligation act" is fit to the vocabulary of the
four workflow specimens on file today, not a formal grammar — a future
specimen it misjudges is a real gap to bring back to the compiler spec, not a silent miss. (The
driver used to route every `led work` call through `./legacy/led`, back when the served boundary
did not yet cover `led work *` — that gap closed at legacy-led-retirement phase 1/1B, and
`hydrate.sh`'s own generated default now runs the served `./led` instead, ledger row 1149/1150;
`drive.py`'s own default is unchanged for a separate, still-open reason — see that generator's own
comment, `tools/workflow_compile.py`.)

## CLI quality-of-life: row-id echo and `judge` auto-layer detection

**Does `led` tell me the id of the row it just wrote?**
Yes, as of `6677b2d` — every `led` write path prints `row <id> written.` on success (e.g. `led
review: row 42 written.`, `led register-principal: row 7 written.`), instead of leaving you to
go find the id with a follow-up query. WITNESSED, against `autoharn1`:
```
$ ./led decision "documentation witness probe (orchlog.d / FAQ authoring task): confirming the
  row-id echo on a live write path; no operational effect intended"
SET
SET
INSERT 0 1
led decision: row 1553 written.
```
**The one disclosed exception:** `led obligate` writes into `countersign_obligation`, whose
primary key is the scope text, not a bigint id — there is nothing to echo, so that one path
stays silent by the same documented convention rather than printing something misleading.

**Does `./judge` still need `--layer` spelled out, or can I just run it?**
As of `f550e54`, bare `./judge` (no `--layer`) auto-detects which of `engine/lp_registry.py`'s
layers the world's schema can actually support and runs every capable one — printing a plain
`INCAPABLE` line (not a red failure) for a layer the world's lineage cannot support, rather than
either crashing on it or silently skipping it. Passing `--layer <name>` explicitly is unchanged:
an incapable target asked for BY NAME still refuses loudly (`QUARANTINED`). WITNESSED, both
forms against `autoharn1` (a world with `s22` work but no `s41` identity, so the `defeat` layer
has no grant substrate here):
```
$ ./judge
# marriage differential -- layer=None (auto-detect capable layers: ['tnow', 'work', 'defeat'])
## layer='tnow'
  [OK ] autoharn1 AGREE              asp=2991 sql=2991 atoms; Δasp=[] Δsql=[]
## layer='work'
  [OK ] autoharn1 AGREE              asp=364 sql=364 atoms; Δasp=[] Δsql=[]
## layer='defeat'
  [--] autoharn1 INCAPABLE          layer='defeat' declared: target has no
       principal_binding_active/principal_competence_activity columns (pre-s41 lineage) --
       the 'defeat' layer has no grant substrate here, capability absent, not record-empty
# DIFFERENTIAL GREEN -- every target bit-identical to the SQL floor

$ ./judge --layer defeat
  [!! ] autoharn1 QUARANTINED        asp=0 sql=0 atoms; Δasp=[] Δsql=[]
          asp QUARANTINED: EDB export failed: CapabilityError: target 'autoharn1' did not
          emit trust_grant/n (capability absent): no principal_binding_active/
          principal_competence_activity columns on this schema (pre-s41 lineage) ...
# DIFFERENTIAL RED -- a target diverged/quarantined (NO RESULT)
```
Exit is red only when a layer that actually RAN [`judge`](../../GLOSSARY.md#judge)s
`DIVERGE_DEFECT`/`QUARANTINED`; a declared-incapable layer never contributes to the exit code
(the same "absence is not a defect" rule the work-item-violations check already applied).

(2026-07-27 correction, root-shim-pruning residue sweep, ledger row 1357: both WITNESSED
transcripts in this section cite commits/row 1553 that predate the umbrella-CLI scaffold
migration, rows 1365/1366/1367, 2026-07-26, which retired the bare `./led`/`./judge` shims
these transcripts typed — left as the dated record they are; the current equivalent
invocations are `./autoharn led decision "..."`, `./autoharn judge`, `./autoharn judge --layer
defeat`.)

## `led` help tokens, `--json` payload mode, and `work list`'s default filter (led.tmpl trio)

Three small `led` changes landed together at commit `abba0dd` (build `a2c2a5f`, fixup `cf51542`,
delivery record: ledger row 1562). None of them touch the kernel — all three live entirely in
`bootstrap/templates/led.tmpl`, so (unlike the [s40/s41](IDENTITY-AND-AUTHORITY.md#granting-and-revoking-a-principals-authority-s40s41)/[s42/s43](EVIDENCE-AND-TRUST.md#recording-verdicts-and-refusals-as-typed-queryable-ledger-entries-s42s43) entries) they are available
to **any** world scaffolded from this commit or later, including this checkout's own `autoharn1`.

**Can I ask `led` for usage without accidentally writing a row?**
Yes. `'help'`, `'-h'`, or `'--help'` as the FIRST word of the statement prints usage to stderr and
writes nothing on every writing subcommand — but the exit code is 0 only once each subcommand's
own arg-count guard has already been satisfied; see the `led review --help` item just below for
the one case where that guard fires first. This includes `led decision --help` specifically (the
one case a prior pass had missed: `--help` used to fall into the
generic unrecognized-flag refusal instead of the same usage-and-exit-0 teach every other
subcommand's `--help` gets). WITNESSED, `autoharn1`, row count unchanged across all three forms
(`--recent 1`'s leading id was `1567` before and after):
```
$ ./led decision --help
usage: led [flags] <kind> <statement...>   (see top-of-file comment for the full flag list: ...)
       led --recent [N] | led current [N] | led show <id> | led question-status | ...
       ...
       '--help'/'-h'/'help' as the FIRST word of <statement...> prints this usage and writes nothing
$ echo $?
0
```
(`led decision help` and `led decision -h` were run the same way — same zero-write result, same
exit 0.)

**Does the same closure cover `led review --help`?** Only once `review`'s three required
positionals are already present ahead of the token. WITNESSED, `autoharn1`, row count unchanged
(`1567` before and after):
```
$ ./led review --help
usage: led review <entry-id> <verdict> <independence> [--antecedent id] <statement...>
       verdict: attest|attest_with_reservations|refuse
       independence: self-review|technical|managerial|financial
       set LED_ACTOR=<principal-name> to countersign as a registered principal
$ echo $?
1
```
A bare `led review --help` (or `-h`/`help`) hits `review`'s pre-existing `$# -lt 4` arg-count
guard (`bootstrap/templates/led.tmpl` ~line 2501) before `check_help_or_dash_first_word` (line
2506) is ever reached — `--help` alone leaves only 1 positional, short of the 4 the guard wants
(entry-id, verdict, independence, statement). It is zero-write either way (usage on stderr, row
count unchanged), but the exit code is **1**, not 0. The exit-0 path only fires once the three
positionals precede the token:
```
$ ./led review 1 attest self-review --help
usage: led review <entry-id> <verdict> <independence> [--antecedent id] <statement...>
       verdict: attest|attest_with_reservations|refuse
       independence: self-review|technical|managerial|financial
       set LED_ACTOR=<principal-name> to countersign as a registered principal
$ echo $?
0
```
So the help-token closure is complete for `decision` and the other pure-help-anywhere
subcommands, but not yet for `review`'s bare `--help`/`-h`/`help` form — a genuine gap in
`led.tmpl`, not a doc error to paper over.

**What if the first word is dash-leading but not actually a help token?**
It REFUSES, teaching, rather than silently committing the word as statement prose — the same
closure this item's title names. WITNESSED, `autoharn1`, row count unchanged (`1567` before and
after):
```
$ ./led note -weirdflag "rest of statement"
led: REFUSED -- the statement's first word '-weirdflag' is dash-leading, which reads as
  a misplaced or mistyped flag rather than intended statement prose (item
  led-help-token-closure -- the same shape refuse_flag_in_statement forecloses for
  KNOWN led flag tokens anywhere in the statement; this closes the gap for an
  UNKNOWN dash-leading FIRST word, which used to sail through and commit a garbage
  row). NOTHING was written. ...
$ echo $?
1
```
Only the FIRST word is checked (the same first-word/whole-word bound `refuse_flag_in_statement`
already uses elsewhere) — a dash-leading word later in the statement is untouched; reword or
quote it if it is genuinely intended prose.

**Can I write ledger rows as JSON instead of a prose statement?**
`led --json <ledger|review|registration|obligation> <file|->` routes a JSON object straight to
the matching s43 [write boundary](../../GLOSSARY.md#write-boundary) function
(`ledger_write`/`review_write`/`registration_write`/`obligation_write`) — the exact same four
functions that "The ledger boundary service (`serving/`)" section above (editorial fix at the suite's legibility loop: the original said "below", wrong-direction even pre-split — the residue filing anticipated exactly this deliberate correction) documents for its own HTTP
endpoints, so the payload shape is the one documented there (payload keys are the target table's own
column names, verbatim, no second vocabulary). Validation at this layer is well-formedness and
top-level-shape only (parses as JSON, is an object) — everything else is the kernel's own
judgment, and its refusal or acceptance comes back as a [typed verdict](../../GLOSSARY.md#typed-verdict),
surfaced verbatim, never paraphrased. The raw payload is size-bounded at 1 MiB
(`MAX_WRITE_BODY_BYTES`, the same bound the HTTP boundary service enforces on its own body), 
checked twice — once on the raw bytes before JSON parsing, once on the re-serialized (compacted)
form before it reaches `psql` — so a payload that only grows past the bound on reserialization is
still caught.

**Prominent caveat, same shape as the [s42/s43 entry](EVIDENCE-AND-TRUST.md#recording-verdicts-and-refusals-as-typed-queryable-ledger-entries-s42s43) (in the evidence-and-trust recipes):** `--json` maps onto the s43 boundary
functions with deliberately NO pre-s43 fallback — a world whose
[birth chain](../../GLOSSARY.md#birth-chain) predates commits `1fc4e8c` (s42) / `84729de` (s43)
refuses `--json` outright, `capability_absent`, before ever reaching the size bound or the
kernel. `autoharn1` (this checkout's own live world) is itself pre-s43, so everything below the
line is what this world can actually show; the size-bound checkpoints and a live typed-verdict
round trip are UNWITNESSED here for that reason and are covered instead by
`seen-red/led-json-payload-mode/run_fixtures.py`'s banked evidence and
[orchlog.d/s42-s43-typed-verdicts.md](../../orchlog.d/s42-s43-typed-verdicts.md).

WITNESSED, `autoharn1`, all zero-write (row count `1567` before and after every case below —
argument validation and the capability check both run before `kernel_write` is ever called, so
none of these reach a place that could write):
```
$ ./led --json bogus /tmp/whatever.json
led --json: REFUSED -- usage: led --json <ledger|review|registration|obligation> <file|->
  '<surface>' selects which s43 boundary function ... Got: 'bogus'.

$ ./led --json ledger /tmp/does-not-exist.json
led --json: REFUSED (capability_absent, naming s43) -- this world's kernel does not
  carry kernel/lineage/s43-typed-verdict-write-boundary.sql, mirroring the FastAPI
  boundary service's own pre-s43 refusal ... Use the ordinary prose CLI on this world instead.
```
The same `capability_absent` refusal fires regardless of what the file contains or how large it
is (missing file, malformed JSON, a JSON array instead of an object, and a 1.2 MB oversized
payload were all tried live and all produced the identical capability check, before file
existence or size is ever inspected) — on this world, `--json`'s refusal surface reduces to two
cases: bad `<surface>` word, or `capability_absent`. A world carrying s43 sees the fuller surface
(size-bound refusals, kernel-level unknown-key refusals, and a real accepted write echoing its
row id) — that is the surface `run_fixtures.py` and the boundary-service spec document.

**Does `led work list` show me everything, or just what's live right now?**
By default, just what is open or claimed — closed items are hidden, not deleted; nothing about
the ledger itself changes. `--all` restores the full historical view. WITNESSED, `autoharn1`:
```
$ ./led work list | tail -1
(56 rows)
$ ./led work list | grep -c '| closed'
0
$ ./led work list --all | tail -1
(242 rows)
$ ./led work list --all | grep -c '| closed'
186
```
56 + 186 = 242: `--all` adds exactly the closed rows back, nothing else changes. The choice is
taught in the usage text itself (`led work list [--all]  (work_item_current; default open/claimed
only, --all for the full history including closed)`), and this is a read-verb default only — `led
work asof <timestamp>` and the raw ledger rows remain the complete, unfiltered record regardless
of which view `work list` shows you. An unrecognized flag refuses rather than silently falling
through:
```
$ ./led work list --bogus
usage: led work list [--all]
$ echo $?
1
```
Delivery record for all three items: [orchlog.d/led-tmpl-trio.md](../../orchlog.d/led-tmpl-trio.md).

(2026-07-27 correction, root-shim-pruning residue sweep, ledger row 1357: every WITNESSED
transcript in this section cites commit `abba0dd`/row 1562 and specific row counts (`1567`,
`56`, `242`) captured against `autoharn1` before the umbrella-CLI scaffold migration, rows
1365/1366/1367, 2026-07-26, which retired the bare `./led` shim these transcripts typed — left
as the dated record they are; the current equivalent invocation is `./autoharn led ...` for
every command shown above.)

