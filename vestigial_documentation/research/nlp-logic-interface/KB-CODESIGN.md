# KB CO-DESIGN — the durable store and the interface, constraining each other (2026-07-02)

Companion to `DESIGN.md` and `INTERFACE.md`. The KB is not a warehouse the interface
happens to write into; the two are designed against each other, and this document
records both directions of constraint explicitly: what the store's shape *forces* on
the interface (identity, scrubbing, supersession) and what the interface's functions
*demand* of the store (order, roles, calibration, the WHY rows). This mutual
constraint is the part of the commissioning that could not be delegated; it is
therefore argued, not just declared.

**Standing facts the design builds on.** The `mining` schema is the raw fact substrate
(document → sentence → assertion/entity/temporal, per-logic views over one base) and
stays exactly that. `contra.finding`/`contra.adjudication` are the adjudication wire
and stay the widget's consumer surface. The harness DB's operational stores are "one
claim-ledger shape" (append-only rows; corrections supersede, never rewrite — the
`tlab_reading`/`tlab_finding` split of ADR-0011's 2026-06-24 amendment). Durable
storage of `~/.claude`-derived claims is **ruled approved** with the scrub boundary
retained (HOOK-DESIGN §4). One standing negative lesson is load-bearing here:
`trace.finding` — the interpretation half of a measurement/interpretation split —
sits at **zero rows against 119 484 spans**. An interpretation layer that is merely
*available* goes unpopulated; this KB therefore makes its authored layers the
side-effect of flows that already run (adjudication verdicts, R-SUP routing), never a
separate act of virtue.

## 1. Shape decision — a new `kb` schema, claims as first-class rows

The claim ledger is a **new schema** (`kb`), not new columns on `mining.assertion`:

- `mining` is per-document raw extraction with its own lifecycle (`DROP SCHEMA …
  CASCADE` rewind; batch loads; the Gutenberg PoC lineage). Session claims have a
  different lifecycle (append-only, never rewound — auditability), different
  provenance (session/turn, not document/sentence), and the scrub boundary. Grafting
  ledger semantics onto a rewindable substrate would make the audit trail exactly as
  durable as the least durable thing sharing its schema.
- Where a `kb.claim` *was* derived from a `mining` row, it says so
  (`mining_assertion_id` nullable FK-by-value, no CASCADE — the ledger outlives the
  substrate); claims from hook ingress carry transcript provenance instead. One claim
  shape, two admission paths, both explicit.

## 2. The mutual constraint, direction 1: the store forces the interface

**Identity.** The KB's primary key is the interface's `ClaimHandle` (INTERFACE §5) —
content-hash over (scrubbed text, canonical keys, provenance triple). Consequences
flowing *back* into the interface, which is why identity lives there and not here:

- Ingest idempotency for free: re-reading a turn upserts the same handle (the ruled
  claim-identity `(session_id, line_index, unit_index, content_hash)` is *inside* the
  hash) — re-work never duplicates.
- The hash is over **scrubbed** text: the scrub boundary (`contra_app._SCRUB`'s
  pattern class, promoted to a shared home when increment 3 wires it) runs *before*
  identity exists, so an unscrubbed variant of a row is unrepresentable in the ledger,
  not filtered from it. The authoritative raw text stays in the transcript; the DB
  holds the derived claim + the pointer (session/line/unit) — the ruled option (a).
- A handle collision is a **write-time loud refusal** (UNIQUE + content comparison on
  conflict), never a silent merge (ADR-0002; INTERFACE §5's sizing argument).

**Supersession.** The store's append-only law forces the interface to express every
correction as a *new* claim plus a link — which is exactly F1's R-SUP output shape.
The engine does not "update" anything; it proposes `supersedes` edges.

## 3. The mutual constraint, direction 2: the functions dictate the tables

```sql
CREATE SCHEMA IF NOT EXISTS kb;

-- The claim ledger (F1–F5's substrate). Append-only; no UPDATE path exists.
CREATE TABLE kb.claim (
    handle          text PRIMARY KEY,          -- ClaimHandle, 12 hex
    session_id      text NOT NULL,
    line_index      int  NOT NULL,
    unit_index      int  NOT NULL,
    turn_index      int  NOT NULL,             -- ClaimProvenance.turn_index (per-session total order)
    role            text NOT NULL,             -- Role enum value; CHECK-constrained
    subj_key        text NOT NULL,
    pred            text NOT NULL,
    obj_key         text NOT NULL,
    negated         boolean NOT NULL,
    sent_text       text NOT NULL,             -- SCRUBBED surface form
    number          double precision,          -- Claim.number (surface parse)
    quantity_dim    text,                      -- Dimension enum value, or NULL
    quantity_base   double precision,          -- Quantity.base_value, or NULL
    mood            text,                      -- Mood enum value, or NULL = unclassified
    hedge           text,                      -- Hedge enum value, or NULL
    standard_index  text,                      -- F4's recovered standard, or NULL
    mining_assertion_id bigint,                -- derivation pointer where applicable
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- Supersession (F1). Append-only edges; authored (adjudicated) or engine-proposed.
CREATE TABLE kb.supersedes (
    later_handle    text NOT NULL REFERENCES kb.claim(handle),
    earlier_handle  text NOT NULL REFERENCES kb.claim(handle),
    origin          text NOT NULL,             -- 'R-SUP' | 'adjudicated' | 'authored'
    reason          text NOT NULL,             -- 'correction' | 'retraction' | 'refinement'
    created_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (later_handle, earlier_handle)
);
-- current-belief view: claims no accepted edge supersedes (the tlab_finding idiom).

-- Findings (all rules). Identity = rule + unordered handle pair (INTERFACE §5).
CREATE TABLE kb.finding (
    rule            text NOT NULL,
    handle_a        text NOT NULL REFERENCES kb.claim(handle),  -- handle_a < handle_b
    handle_b        text NOT NULL REFERENCES kb.claim(handle),
    value           text,                      -- paraconsistent value ('both') where one exists
    grounding       text NOT NULL,
    extra           jsonb NOT NULL DEFAULT '{}',
    first_seen      timestamptz NOT NULL DEFAULT now(),
    last_seen       timestamptz NOT NULL DEFAULT now(),
    seen_count      int NOT NULL DEFAULT 1,    -- re-observation bumps; NEVER a second row
    PRIMARY KEY (rule, handle_a, handle_b),
    CHECK (handle_a < handle_b)
);

-- The WHY-ledger (F6). Rows are AUTHORED in v1 (DESIGN §3-F6's scope honesty).
CREATE TABLE kb.mandate (
    mandate_id      text PRIMARY KEY,          -- short slug, human-legible
    statement       text NOT NULL,             -- the decision/means as ratified
    recorded_why    text NOT NULL,             -- the purpose the decision serves
    provenance      text NOT NULL,             -- session/doc pointer to the ratification
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE kb.why_event (
    event_id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mandate_id      text NOT NULL REFERENCES kb.mandate(mandate_id),
    kind            text NOT NULL,             -- 'means_change' | 'reverified' | 'retired'
    detail          text NOT NULL,
    witness         text,                      -- REQUIRED when kind='retired' (trigger-enforced):
                                               -- the failed experiment that retires the WHY
    provenance      text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);
-- kb.why_orphaned view (the SQL differential floor for R-WHY): mandates with a
-- means_change and no subsequent reverified/retired event.

-- Calibration (F4's unresolved gluts; F2's labeled mood data as it accrues).
CREATE TABLE kb.calibration (
    cal_id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    kind            text NOT NULL,             -- 'unresolved_glut' | 'mood_label' | ...
    handle_a        text REFERENCES kb.claim(handle),
    handle_b        text REFERENCES kb.claim(handle),
    payload         jsonb NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);
```

**Adjudication stays in `contra`.** Findings routed to human/LLM adjudication continue
through `contra.finding` (the widget's `_FINDING_COLS` wire is untouched); the KB
finding row records the routing in `extra`. Adjudication verdicts flow back as
`kb.supersedes` edges (`origin='adjudicated'`) or calibration rows — the authored
layers populate as a *by-product of adjudication*, which is the anti-`trace.finding`
design stated in the preamble.

## 4. What the store exposes (the read side the functions consume)

- **current-belief view** — claims minus superseded (F1's output; F9's supply reads
  beliefs, never raw claims, so a corrected claim is unsuppliable by construction).
- **`kb.why_orphaned` view** — the R-WHY differential floor *and* the maintainer's
  direct query surface.
- **supply keys** — indexes on `(subj_key)`, `(pred)`, `(quantity_dim)`, and mandate
  topics: F9's typed-relevance retrieval is index walks, no scan, budget-friendly.
- **the escalation window** — `kb.finding` joined through `kb.supersedes` chains with
  hedge columns: `R-SUP-ESC` is computable as a view first (the SQL floor), an ASP
  rule when defeaters accrue — same assign-don't-compete ladder as R-WHY.
- **audit** — every row carries provenance to a transcript position; the ephemera
  snapshots (`docs/claude-ephemera/`) hold the transcripts; handle+gloss citation
  makes any injected context traceable back to both.

## 5. Reified work units — presented for ratification (new, not re-found)

The maintainer half-remembered a research remark about reifying work units and their
discharges as separate entities; the search confirmed it **absent** from all four
corpora (RESEARCH-SUMMARIES, final section — nearest neighbors: the COMMIT-lifecycle
"as one object" gap; the `audit_log` row-history pattern). So this is proposed as a
*new* shape, the maintainer's to ratify, sized minimally for F7:

```sql
CREATE TABLE kb.work_unit (
    unit_id     text PRIMARY KEY,              -- slug ('adr-read:0012', 'port-contract:x')
    kind        text NOT NULL,
    detail      text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE kb.discharge (                    -- the SEPARATE entity: a unit may be
    discharge_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,   -- discharged 0..N times
    unit_id     text NOT NULL REFERENCES kb.work_unit(unit_id),
    witness     text NOT NULL,                 -- what evidences the discharge
    provenance  text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE kb.prereq (
    unit_id     text NOT NULL REFERENCES kb.work_unit(unit_id),
    requires    text NOT NULL REFERENCES kb.work_unit(unit_id),
    PRIMARY KEY (unit_id, requires)
);
```

The separation (unit ≠ discharge, discharge carries its own witness and provenance)
is what makes "touched before discharged" (R-ORD) and "claimed done without witness"
(the ADR-0013 amendment's shape) *queries* rather than reconstructions. Cost: three
small tables and the authoring burden; the ledger only pays off if units are logged
by instruments, not by hand — which is why R-ORD's v1 substrate (BUILD-PLAN increment
4) is the *hook's own* mechanical events (ADR files read, gates run), not free-form
task tracking.

## 6. Two writers of one truth — the Python/SQL boundary, mechanized

The DDL above and the interface's types describe the same facts (Role, Mood,
Dimension values; the claim column set; the handle format). That is a cross-boundary
fact under ADR-0012 P7: **one authoritative definition, every side derives**. The
Python types are the authority (they are the richer artifact and the `mypy --strict`
surface). Enforcement, at the strongest proportionate rung:

- a **schema-parity test** (increment 3, shipped with the DDL — the net ships with
  the first fix, ADR-0011's 2026-07-02 amendment): introspects `information_schema`
  against the dataclass/enum definitions — column set, CHECK-constraint vocabularies
  == enum values, nullability == `Optional`ity. Negative control: a mutated enum
  member must go red.
- CHECK constraints on `role/mood/hedge/quantity_dim` are **generated** from the
  enums by the migration script, not hand-typed — derive-don't-re-author where the
  contract is static.
- Full codegen (types → DDL) is deliberately *not* built at N=1 migrations; the
  parity gate is the floor, and the third schema consumer is the named trigger
  (ADR-0012 Revisit #3's shape) — a filed level choice, not a scale excuse: the gate
  exists from day one, only the generator is deferred.

## 7. Retention, size, and the envelope

At measured densities (~8×10³ claims per corpus sweep; a working session produces
10²–10³ claims) the ledger grows by megabytes per week — no partitioning needed at
this horizon; the honest envelope statement is an `AdvertisedLimits`-style row-count
watermark in the loader's log (ADR-0016's advertise-before-refuse posture applied to
ourselves), with the first real pressure the trigger for a retention ruling
(maintainer's, not the executor's — sessions are audit material, and pruning audit
material is never a default).
