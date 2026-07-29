# FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC — the medium in which blindness is a property

<!-- doc-attest-exempt: Fable-authored spec 2026-07-29, status=proposed, AWAITING MAINTAINER
RATIFICATION -- authored under durable rows 567 (flow control is the head requirement), 608
(reviewer blindness is the first named consumer), 614 (the rising-sea register and the three
delegated adjudications), 532 (DAC is the floor, RBAC wanted), and the S1-S6 adjudication rows
598-606. The A:B:C loop runs on the build, not this text. Removal condition: the ratification
row or the build's merge record supersedes this exemption. -->
<!-- design-currency: status=proposed depends-on=FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md -->

The maintainer's own words govern (durable rows 567/608, verbatim there): access control's
most important deliverable is *control over how information can travel in the system*, and
its first named consumer is that *reviewers should be guaranteed not to understand the
rationale for their being there*. This spec designs the general medium, not the feature:
identity on every request and scoped visibility as first-class concepts, after which
reviewer blindness, export redaction, and counterpart scoping are instances, not builds.

## 1. The two concepts the medium adds

**1a. Identity on the read path (serving layer, mergeable era).** Every boundary request —
GET and POST alike — resolves an identity through the channels the write path already has
(vendor stamp headers; minted-principal header; else `anonymous`). Reads are NEVER refused
for anonymity in the default posture: an anonymous read simply resolves to the world's
**open scope** (everything the registry serves today, byte-identical behavior). What
changes is only that the resolution is *performed and journaled* — the read-observer
channel gains who-read-what, which is the witness half of every guarantee below. This is
additive: no client changes, no new refusal class, `/meta` advertises the capability.

**1b. Scopes as first-class, ledgered objects (kernel delta, future birth).** A **scope**
is a named, ledgered visibility predicate: a set of granted read surfaces (views/routes
from the registry's own closed vocabulary) plus an optional row-level exclusion family
(by kind-class, by thread, by work-item lineage, by explicit row set). One new kind
(`principal_scope_bound`, an authority-bearing act class under s60's own gating), one
derived view (`principal_scopes`), and the default that makes it fail-safe: **a principal
with no bound scope holds the open scope** — an unarmed world is byte-identical.
Scope semantics are EXCLUSIONARY over content: a scoped-out row's content never crosses
the boundary to that principal; its existence is disclosed as a typed redaction marker
(`{id, redacted: true, scope}`) so pagination, counts, and the hash-chain's shape stay
honest — hiding existence would make every count a lie, and the panel's own C6 discipline
(empty vs absent) applies to us too. Blindness is to *content and rationale*, not to the
row-count of the universe; the one place existence itself anchors (a redaction marker
"regarding YOU") is named in §4's not-covered list rather than papered over.

## 2. Enforcement points, layered honestly

- **Boundary-side filtering (first, serving layer):** the conduit applies the resolved
  principal's scope to every read route — registry views, row routes, history walks,
  SSE (a head-signal leaks only ids; ids are existence, disclosed above). One home:
  the same seam `get_all_rows`/the registry wrapper already funnels through.
- **Postgres RLS (the end state, kernel-grade, future birth):** rests on the S2b
  three-identity split (row 600: superuser at birth only; non-login owner role owning
  schema + definer functions; login access role) — RLS policies keyed on a per-request
  `SET`-scoped principal are only real once the connecting role is not the owner. The
  slot is named; the boundary filter is not a temporary hack but the layer that serves
  multi-world scoping regardless (RLS cannot see a counterpart world's courier pull).
- **The side-channel honesty (composition with what exists):** flow control binds
  boundary-mediated access. A same-user agent with raw psql or filesystem access walks
  around it — and the project already forecloses that for governed agents by mechanism:
  the raw-SQL ban (`hooks/pretooluse_sql_block.py`) and the change-gate/sweep pair make
  the boundary the only sanctioned data path for a dispatched agent, and the read
  observer witnesses the rest. The guarantee is therefore stated as: *a governed,
  hook-policed principal cannot receive scoped-out content through any sanctioned
  channel, and unsanctioned channels are loud* — which is the same grade of guarantee
  every enforcement surface in this project honestly carries (tripwire-bounded, not
  cryptographic), per s17's own LIMITS register.

## 3. The first instance: reviewer blindness (the walnut that falls open)

A dispatch that mints a reviewer principal binds, in the same act, a scope excluding the
commissioning lineage: the work item's opener/decision rows, the finding rows that
motivated the review, the orchestrator's thread — expressed by lineage predicate
(`exclude: work-item <slug> commissioning-class rows`), not by hand-enumerated ids.
The reviewer's `led`/boundary reads then *cannot* return the rationale, however careless
the brief; the read journal witnesses what it did read; and the verdict's independence
claim gains, for the first time, mechanical corroboration: the kernel can state not just
"distinct stamp pair" (the s21 proxy, row 392's disclosed bound) but "no sanctioned read
of the excluded set occurred." Unanchored-by-discipline becomes unanchored-by-scope.
The same abstraction, unchanged, then serves: counterpart-world missive scoping (a
courier principal scoped to its thread), export redaction (an asof-export invoked under
a scope emits redaction markers), and any future second-party read tier — none of which
this spec builds, all of which the medium admits without new concepts.

## 4. Closure statement (ADR-0000 Rule 2(a))

**Invariant:** for every read-shaped act by a scoped principal through a sanctioned
channel, the content of scoped-out rows does not reach the principal, every such
non-delivery is a typed, journaled redaction, and every delivery is journaled to the
read-observer channel attributable to the resolved identity.

**Quantification universe** — read surfaces enumerated: boundary GETs (registry views,
row routes, history, asof, credited, artifacts), SSE head-signals (ids only — existence),
the CLI (an HTTP client of the same routes since the served rebase), courier pulls
(counterpart-boundary GETs), asof-export artifacts, fossil exports (the resolver of the
fossil-and-backup spec inherits scope at read time), `/attestation` and `/meta`/`/health`
(capability metadata: open-scope always, disclosed). Identity channels: vendor stamp,
minted principal, anonymous — the three s43 already admits.

**Named as not covered, deliberately:** the independent instruments (verify-chain, judge,
audit, doctor — direct-psql by the two-trust-roots ruling; a scoped principal simply
cannot run them, disclosed, and their verdicts arrive via the already-labeled banked
surface); the superuser and any same-user unsanctioned channel (tripwire-bounded, §2);
existence-anchoring via redaction markers regarding oneself (a real residue: knowing
*that* a rationale exists is weaker anchoring than reading it, accepted and stated);
multi-user trust (durable row 31 stands — every principal here is one operator's; scopes
partition *context*, not *trust*); crypto (slots named, deferral honored).

**Denomination check:** scopes are denominated in the ledger's own vocabulary (kinds,
threads, work-item lineage, registry surface names) — never in row-id arithmetic or
byte offsets, which are proxies that drift.

## 5. Mechanism roster and sequencing

1. **S2b three-identity split** (scaffold, future births; row 600) — the foundation.
2. **Read-path identity resolution + read journaling** (serving; mergeable now).
3. **`principal_scope_bound` kind + `principal_scopes` view + boundary filter**
   (kernel delta + serving; the delta rides the s70 batch or its successor).
4. **Dispatch-time scope minting** (`dispatch mint --scope ...`; CLI, after 3).
5. **S3 stamp-binding conjunct** (row 601, with its s21 corrections) — orthogonal,
   same batch family; RBAC's authenticated input.
6. **RLS slot** (future birth, after S2b lands in a chain; named, not built).

Witness plan, both polarities on scratch, red first: a scoped reviewer's read of an
excluded row returns the redaction marker never the content; the same read by an
unscoped principal returns content byte-identical to today; the read journal carries
both; an unarmed world's every route byte-identical (the S1-family regression bar);
dispatch-minted scope witnessed end-to-end on a scratch review loop.

## License

Public Domain (The Unlicense).
