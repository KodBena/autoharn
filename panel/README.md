# The Maintainer Co-Sign Panel — operator walkthrough

This page is for the maintainer running `panel/` on his own machine to follow tracked
commissions live and co-sign what an agent has formally claimed. It answers one question:
*what do I type, and what should I see, to go from a clean checkout to reading a commission
item-by-item and putting my name on one.* It assumes nothing about the panel's internals — that
design lives in this build's own commissioned spec (not itself a committed repo file) and in
`panel/backend`/`panel/frontend`'s own module docstrings, not this page's job.

**Known blocking gap, verified while writing this page (§3 has the reproduction and the fix
needed) — read this before you try §3.** Opening `panel/frontend/index.html` as shipped does
NOT currently work: the frontend's API calls are root-relative (`/api/health`, etc.) and only
resolve when the page is served from the SAME origin as the backend, which the backend does not
yet do (no static-file mount). §3 below documents the failure exactly as observed, not as
hoped, and a tracker item (`panel-frontend-same-origin-serving-gap`, §9) names the fix — outside
this page's authoring scope (it touches `panel/backend`/`panel/frontend` source, which this
build does not touch).

The panel is a small, self-contained web page plus a local API server. It reads the project's
decision ledger (the append-only record `./led`/`./pickup` already write to) and renders it as
something you can scan and act on; the one thing it can *write* is a co-sign, and it writes that
the same way you would type it yourself: through `./led review`. Nothing here bypasses the
ledger's own rules — a refusal you would get from the command line is a refusal you get from
this page too, shown to you verbatim.

## 1. Before you start — resolving where the ledger lives

The panel never asks you for a host or a database name; it reads the same `deployment.json`
your other verbs (`led`, `pickup`, `judge`) already read, via `filing/deployment_record.py` +
`filing/pghost_resolve.py` — the one place this project resolves "which Postgres, which schema."
If that file is missing or unreadable, the panel refuses to start rather than guess (you'll see
a Python traceback naming the missing file, not a silent connection to the wrong place). You do
not need to do anything here if `./led` already works in this checkout — the panel reuses the
exact same resolution.

**What you need installed once, before the first run:**

```
python3 -m pip install --user fastapi 'uvicorn' 'psycopg[binary]'
```

(Or `python3 -m pip install --user -r panel/backend/requirements.txt`.) This is a one-time
step per machine; skip it if these are already on your `PYTHONPATH`.

## 2. Start the backend

From the repository root:

```
cd panel/backend
python3 -m uvicorn app:app --host 127.0.0.1 --port 8420
```

What you should see:

```
INFO:     Started server process [NNNNN]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8420 (Press CTRL+C to quit)
```

(WITNESSED against the live `autoharn1` deployment while writing this page — the exact banner
above, port 8420, the one `config.py`'s `DEFAULT_BIND_PORT` names.) The server binds to
`127.0.0.1` only — nothing outside your own machine can reach it, and there is no login screen,
because there is nobody else this page is written for. If you need a different port, set
`PANEL_BIND_PORT` before starting it (the bind itself is still yours to enforce — the command
above is what actually opens the socket; `PANEL_BIND_PORT` only changes which port it asks for).

At startup the backend also registers the `maintainer` principal against your ledger, if it
is not already registered — idempotently, the same `ON CONFLICT DO NOTHING` `./led
register-principal` would do by hand. You will not see this fail unless `./led` itself is
broken; if it does fail, the server refuses to finish starting and names the exit code and
`./led`'s own stderr.

A quick sanity check, in a second terminal, while the server above keeps running:

```
curl -s http://127.0.0.1:8420/api/health
```

What you should see (WITNESSED, live):

```json
{"ok":true,"deployment":{"schema":"autoharn1","db":"toy","host_resolved":true},
 "stamp_secret_armed":false,"maintainer_principal":"maintainer",
 "verdicts":["attest","attest_with_reservations","refuse"],
 "independence_values":["self-review","technical","managerial","financial"]}
```

`stamp_secret_armed: false` here means what §8 below explains: this deployment has not armed
the interception-stamp mechanism, so only `self-review` co-signs will succeed. That is normal,
not an error.

## 3. Open the SPA — CURRENTLY BLOCKED, verified, do not skip this section

`panel/frontend/` is fully self-contained (no build step, no CDN — everything it needs is
inlined or vendored across its three files), and the natural thing to try is opening
`panel/frontend/index.html` directly in a browser. **As shipped, this does not work.** Verified
while writing this page (headless Chromium, `--dump-dom`, against a live backend on
`127.0.0.1:8420`): the page loads, then immediately shows

```
Failed to load panel: Failed to fetch
```

**Why:** `panel/frontend/app.js` calls its backend with root-relative paths (`fetch("/api/health")`,
`fetch("/api/commissions")`, etc. — by design, so it never hand-codes a host/port, see the file's
own header). A root-relative fetch resolves against the *document's own origin*. Opened via
`file://`, the document's origin is the `file://` scheme itself — there is no `127.0.0.1:8420` to
reach, and the browser refuses the request before it goes anywhere. `panel/backend/app.py`, as
committed, mounts no static-file route of its own, so there is currently no way to serve
`index.html` from the *same* origin as the API without a code change.

**The fix this needs (out of this README's scope — it is a `panel/backend`/`panel/frontend`
source change, and this build does not touch that source):** either (a) have `app.py` mount
`panel/frontend/` as static files at `/`, so opening `http://127.0.0.1:8420/` serves the SPA from
the same origin the API already answers on, or (b) give the frontend a configurable absolute API
base URL plus a CORS allowance on the backend. Filed as `panel-frontend-same-origin-serving-gap`
(§9) — this is a genuine blocker for using the panel as a browser page at all, not a cosmetic
gap, and the next builder who touches `panel/backend`/`panel/frontend` should treat it as the
first thing to close.

**Until that lands**, the panel's read/write surface is still fully exercisable directly against
the API with `curl` (every example in §4–§6 below shows the exact request/response you'd see),
and the scratch-schema fixture (`seen-red/panel-cosign/run_fixtures.py`) exercises the co-sign
write path end to end without a browser at all. There is no working browser-page path to
document honestly until the mount (or equivalent) lands.

## 4. Pick a commission and read it item by item

The rest of this walkthrough (§4–§6) describes the SPA's designed behavior — accurate against
the live API today (every JSON example below is real, WITNESSED output) but reachable through a
browser page only once §3's blocking gap is closed. Until then, the same reads/writes are the
`curl`/fixture calls shown alongside each example.

The landing view lists every commission on the ledger (`GET /api/commissions` — any
`kind='commission'` row, not only the one this build was commissioned to render: the panel is
not a single-commission product, per the hard constraint that started this build). Pick one —
for a first look, the commission this build itself was commissioned against, ledger row 680
("MAINTAINER EXECUTIVE RESPONSE 2026-07-14"), is already decomposed and worth reading.

What you get is the commission's own verbatim text (read live from the ledger row itself —
never a stored copy that could drift from it) followed by one row per decomposition item: a
short label an agent wrote, a status, and the witnesses (earlier ledger rows or work items) that
back the label up. WITNESSED against the live deployment while writing this page: commission
680 currently decomposes into 39 items, 38 `WITNESSED` and 1 `OPEN` (`concern-2` — an item an
agent named but has, honestly, no witness for yet; see below for what that means).

**The five states, and what each asks you to do:**

- **`OPEN`** — the item exists (an agent named it) but has no witness that resolves at all, or
  every witness is not yet substantive (e.g. a work item still open, not closed). There is
  nothing to co-sign yet. Action: none is owed from you; if the item should have a witness by
  now, that is a question for whoever owns the underlying work, not something the panel can fix.
- **`WITNESSED`** — at least one witness resolves and is substantive (a closed work item, or any
  resolved ledger row), but nobody has co-signed anything yet. Action: read the witness(es), and
  if you're satisfied, co-sign (§5) — either the item row itself, or an individual witness.
- **`PARTIAL`** — more than one witness exists, and you (the maintainer) have co-signed *some*
  but not all of them individually. Action: read what's still unsigned and co-sign the
  remaining witness(es) if you're satisfied, the same way you signed the first — there is
  nothing special about a partial state except that it is honestly showing you unfinished work,
  not rounding up to done.
- **`COSIGNED`** — either you co-signed the item row itself (the fast path: "I co-signed item
  A1" as one act, regardless of how many witnesses it has), or every one of its witnesses is
  individually co-signed. Both are genuine completions; the panel does not distinguish which
  path got you there in the status itself (both fast-path and per-witness paths are visible in
  the item's own `cosign`/witness detail if you want to know which). Action: none — this is
  discharged.
- **`AMBIGUOUS`** (a hazard banner, not a normal state) — two or more *independent, non-superseding*
  ledger rows claim the *same* decomposition item identity (e.g. two different rows both say
  "I am item A1"). This is a genuine data-integrity problem on the ledger, not a panel bug, and
  the panel refuses to guess which one is right: you will see no single label, no single row id,
  just the list of colliding row ids. Action: **read both (or all) of the colliding rows** (the
  ledger — `./led show <id>` — is the source of truth here, not this page) and decide which one
  is correct; **supersede the wrong one** (`./led --supersedes <bad-id> --refs "..." note "..."`)
  the same way you would correct any other mistaken ledger row. Until you do, either colliding
  row can still be individually co-signed from this page (co-signing does not require the
  ambiguity to be resolved first — see §5), but the item's own label/status stays honestly
  unresolved until the duplicate is superseded.

## 5. Co-sign an item or a witness

Click co-sign on either the item row itself, or on any individual witness that has its own
`cosign_target_row` (a work item's closing row, or a cited ledger row) — the hard requirement
this panel was built to satisfy is that co-sign works on *any* row that bears a witness, not only
the item's own row, and that includes either row of an `AMBIGUOUS` pair.

You pick a **verdict** (`attest`, `attest_with_reservations`, `refuse`) and an **independence**
value (`self-review`, `technical`, `managerial`, `financial`) — both lists are read live from the
backend (`GET /api/health`'s `verdicts`/`independence_values`), never hand-typed into the page,
so they can never drift from what the kernel actually accepts. You write a short basis statement
(what you actually checked, not a rubber stamp — a too-short one gets a warning from `./led`
itself, shown to you the same way).

Behind the click, the panel runs exactly `LED_ACTOR=maintainer ./led review <row_id> <verdict>
<independence> <basis>` — the same command you would type by hand. **Whatever comes back is
shown to you verbatim** — stdout, stderr, and the exit code — never paraphrased, never silently
retried, never turned into a fake success. WITNESSED (scratch-schema fixture,
`seen-red/panel-cosign/red.txt`, both cases real, live-ledger output):

- A **self-review attest** against your own scratch note row succeeds and reads back cleanly:
  `maintainer_cosigned(item_row) = {'review_id': 3, 'verdict': 'attest', 'actor_name': 'maintainer'}`.
- A **`managerial` co-sign attempted on an unstamped deployment is refused by the kernel itself**,
  and the panel shows you that refusal's own words, unedited:

  ```
  ERROR:  Ledger policy: a review claiming independence (managerial) must carry a VERIFIED
  interception stamp — an unstamped review cannot establish it was a distinct invocation.
  Record independence='self-review' if you reviewed your own work, or write the review
  through a genuinely distinct stamped invocation (a separate agent).
  ```

If you pick a verdict/independence value the kernel does not recognize at all (a typo, not a
real refusal), the panel stops you before it even shells out (`400`, naming the allowed values)
— but it never pre-blocks a *combination* the kernel would refuse for a substantive reason (like
`managerial` above): that refusal is real, and you are meant to see it, not have it hidden from
you by an over-eager client-side guess.

## 6. The independence note, read honestly

`self-review` is the only independence value that will ever succeed against this deployment
right now, because `stamp_secret` (the mechanism that would let the kernel *verify* that a
review was written by a genuinely separate invocation) is unarmed here (§1's health check told
you this). That is not a defect in the panel — it is an honest statement about what this
deployment can currently prove. What actually makes your co-sign meaningful today is simpler and
still real: **you (`maintainer`) are a different, registered ledger principal from the agent
(`author`) whose row you are signing** — the segregation-of-duties check the kernel enforces on
every review (a principal can never countersign its own row) is what your co-sign discharges,
independent of whether the *independence value* you picked can be cryptographically proven. The
panel labels a `self-review`-grade endorsement exactly as what it is: "endorsement (self-review
grade — independence not stamp-attested; actor: maintainer)" — never dressed up as more than
that.

**If you later arm `stamp_secret`** (a maintainer act, out of this panel's scope — it is a
kernel-level operational decision, not a button here), `technical`/`managerial`/`financial`
co-signs become genuinely provable, and the panel needs no code change to start honoring them:
it already reads the kernel's own vocabulary live (§5) and already lets the kernel's own
`validate_independence` trigger decide what succeeds. Arming the stamp is documented here as the
upgrade path that exists; this build does not implement arming it, and does not need to.

## 7. Keeping the view live

There is no database trigger that pushes a ledger change to this page the instant it happens —
adding one would mean editing a frozen kernel/template surface, which this build (like
everything else in `panel/`) does not touch. Instead, the backend polls
`SELECT max(id), max(ts), count(*) FROM ledger` on a short interval (`PANEL_POLL_INTERVAL`,
default 2 seconds) and pushes a "something changed" event over Server-Sent Events to every open
tab the moment the watermark moves — so in practice a co-sign you make in one tab, or a `./led`
write you make from a terminal, shows up in every other open tab within about that interval,
not instantly. If your browser tab's SSE connection drops (a laptop sleep, a network blip), the
page falls back to polling `/api/watermark` itself until the stream comes back. Either way, if a
page ever looks stale, a manual reload always shows the true, current ledger state — the polling
is a convenience, never the source of truth.

## 8. What this page does not cover

The commission-680 view (§4's worked example) is one page this build renders, not the product's
scope — pick any other `kind='commission'` row from the landing list and you get the identical
item-by-item treatment. The panel has no notion of "the one commission it knows about."

Three residuals this build named rather than silently building around (filed as tracker items,
§9): the independence vocabulary cannot yet express "a genuine executive endorsement whose
independence is not stamp-provable" as anything other than `self-review`-labeled-honestly; a
future optional live character-span locator from an item's label back into its exact slice of
the commission's own text is not built; and a near-duplicate host-resolution module
(`instruments/pghost_resolve.py`) sits alongside the one this panel actually uses
(`filing/pghost_resolve.py`) and should eventually become a thin re-export rather than a second
copy — this panel already points at the right one; de-duplicating the other is a separate,
out-of-scope act.

## 9. Filed tracker items

- `panel-cosign-independence-grade` — the independence vocabulary's residual gap (§6), composing
  with `design/MAINT-COUNTERSIGN-CLOSE-SEMANTICS-SPEC.md`'s Element C grade.
- `panel-item-span-anchor` — a future live character-span locator from an item's label into the
  commission's own text (§8).
- `pghost-resolve-duplicate-home` — `instruments/pghost_resolve.py` should re-export from
  `filing/pghost_resolve.py` rather than duplicate it (§8; flagged, not fixed here — out of this
  build's scope, touches `instruments/`'s other possible consumers).
- `panel-frontend-same-origin-serving-gap` — (§3, discovered while writing this page, not a
  residual named by the build spec) the SPA cannot be opened as a browser page as shipped;
  `app.py` needs a static-file mount (or the frontend needs an absolute API base URL plus CORS)
  before `panel/frontend/index.html` can reach the backend at all. This is a blocking gap for
  the panel's basic operation, not a cosmetic one.

<!-- doc-attest-exempt: no forking-capable tool (an Agent/Task tool distinct from this session)
was available in this WP-4 invocation to run the A:B:C fresh-context loop -- removal condition:
run the A:B:C loop the next time a forking-capable session touches this file (SCHEMA.md /
ledger rows 699,714 precedent for this same marker shape). -->
