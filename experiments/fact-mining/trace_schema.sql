-- experiments/fact-mining/trace_schema.sql
-- EPHEMERAL distributed-trace store for the 3-process coref pipeline.
-- Lives in its own schema so the whole thing wipes with one statement and cannot
-- touch anything else (mirrors schema.sql's mining schema):
--     DROP SCHEMA trace CASCADE;
-- NOT a blessed migration (cf. db/harness/) — a throwaway we keep while we find
-- where the ~22s goes and who blocks on whom.
--
-- ADR-0009 (2026-06-24 amendment) shape: a captured measurement is CODE-STAMPED
-- (run.git_commit/git_tree + exact cmd + config), aggregated as median/IQR (not
-- eyeballed — see trace.span_stats), and the immutable MEASUREMENT (trace.span) is
-- separated from the supersedable INTERPRETATION (trace.finding) at the SCHEMA
-- level, so an overturned perf claim is auditable, not lost.
--
-- ===================== CLOCK-SKEW CAVEAT (read before querying) =====================
-- Two clocks are recorded per span, on purpose, and they answer different questions:
--   * t_start / t_end are WALL-clock (timestamptz). They exist ONLY for CROSS-PROCESS
--     ORDERING (which span started before which, across the client/guest and the two
--     host daemons). The guest and host wall clocks may be SKEWED relative to each
--     other; that skew BOUNDS the ordering resolution — two spans in different
--     processes whose wall times differ by less than the guest<->host offset cannot
--     be reliably ordered. NEVER compute a duration by subtracting a t_end in one
--     process from a t_start in another: the skew corrupts it.
--   * dur_ms is a per-span duration from a MONOTONIC clock, measured entirely WITHIN
--     one process. It is SKEW-IMMUNE and is the accurate duration. Aggregate THIS for
--     "how long did X take"; use the wall pair only to order/overlap across processes.
-- ====================================================================================

BEGIN;
DROP SCHEMA IF EXISTS trace CASCADE;
CREATE SCHEMA trace;

-- ===== the code stamp: one row per traced pipeline run =====
-- Code-addressable (ADR-0009): a reading is meaningless without the exact code +
-- command + config that produced it. Minted by load_facts --trace (spans.begin_run).
CREATE TABLE trace.run (
  run_id     bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  trace_id   text NOT NULL,             -- the root trace id; every span of this run shares it
  git_commit text NOT NULL,             -- HEAD at run time
  git_tree   text NOT NULL,             -- content tree INCL. uncommitted edits (throwaway-index write-tree)
  cmd        text NOT NULL,             -- exact command line that launched the run
  config     jsonb NOT NULL DEFAULT '{}'::jsonb,  -- argv/config (model, backend, max_paras, ...)
  host       text,                      -- where the client ran (clock-skew context)
  started_at timestamptz NOT NULL DEFAULT now()
);

-- ===== the immutable measurement: one row per span =====
-- An INSERT-ONLY reading (ADR-0009): never updated, never reinterpreted in place.
-- parent_span_id is intentionally NOT a foreign key: a span's parent frequently
-- lives in ANOTHER PROCESS (the client's zmq_wait is the nlp_server handle's parent;
-- the nlp_server zmq_wait is the decode handle's parent) and may be flushed at a
-- different time, so cross-process parent integrity cannot be a DB FK. It is a soft
-- link resolved at query time within (run_id, *).
CREATE TABLE trace.span (
  span_pk        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id         bigint NOT NULL REFERENCES trace.run ON DELETE CASCADE,
  trace_id       text NOT NULL,
  span_id        text NOT NULL,
  parent_span_id text,                  -- soft link (often cross-process); NULL for a root
  process        text NOT NULL,         -- 'client' | 'nlp_server' | 'decode_server'
  name           text NOT NULL,         -- e.g. 'client.zmq_wait.nlp_server', 'host_shell.union_find'
  t_start        timestamptz NOT NULL,  -- WALL: cross-process ORDERING only (skew-bounded)
  t_end          timestamptz NOT NULL,  -- WALL
  dur_ms         double precision NOT NULL,  -- MONOTONIC per-span duration; SKEW-IMMUNE, accurate
  attrs          jsonb NOT NULL DEFAULT '{}'::jsonb,  -- cache_hit, k, n_pairs, n_texts, ...
  recorded_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (run_id, span_id)              -- idempotent re-flush (ON CONFLICT DO NOTHING)
);
CREATE INDEX span_by_run    ON trace.span (run_id, t_start);
CREATE INDEX span_by_parent ON trace.span (run_id, parent_span_id);
CREATE INDEX span_by_name    ON trace.span (run_id, process, name);

-- ===== the supersedable interpretation: a CLAIM about the measurement =====
-- Separated from trace.span at the schema level (ADR-0009): "the ~22s is the decode
-- daemon's cold jax compile", "the +Xs was an artifact of cache misses" — these are
-- AUTHORED findings that can be overturned. `supersedes` chains an overturn so the
-- history is auditable, never silently lost. Evidence carries the aggregate it rests
-- on (span name, median_ms, iqr_ms, n) — never a single eyeballed number.
CREATE TABLE trace.finding (
  finding_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id     bigint NOT NULL REFERENCES trace.run ON DELETE CASCADE,
  claim      text NOT NULL,
  evidence   jsonb NOT NULL DEFAULT '{}'::jsonb,
  supersedes bigint REFERENCES trace.finding,   -- the finding this overturns, if any
  author     text NOT NULL DEFAULT current_user,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- ===== aggregation, not eyeballing (ADR-0009 robust-benchmark-statistics) =====
-- median / IQR / n per (run, process, span name). A perf claim cites THIS, never a
-- single span's dur_ms. percentile_cont gives the continuous median and quartiles.
CREATE VIEW trace.span_stats AS
  SELECT run_id, process, name,
         count(*)                                                AS n,
         percentile_cont(0.5)  WITHIN GROUP (ORDER BY dur_ms)    AS median_ms,
         percentile_cont(0.25) WITHIN GROUP (ORDER BY dur_ms)    AS q1_ms,
         percentile_cont(0.75) WITHIN GROUP (ORDER BY dur_ms)    AS q3_ms,
         min(dur_ms)                                             AS min_ms,
         max(dur_ms)                                             AS max_ms,
         sum(dur_ms)                                             AS total_ms
  FROM trace.span
  GROUP BY run_id, process, name
  ORDER BY run_id, total_ms DESC;

-- ===== who blocks on whom: the cross-process wait edges =====
-- A zmq_wait span in process P is P blocked on its peer; its child(ren) (in the peer
-- process, soft-linked by parent_span_id) are the work P waited for. Each peer wraps
-- its handler in ONE per-request root span (decode_server.handle / nlp_server.handle),
-- so a wait has exactly one peer-process child BY CONSTRUCTION and overhead = wait -
-- handle is the real transport + queueing cost. We nonetheless SUM the children here
-- so the view stays correct if a future variant ever fans a wait out to siblings —
-- overhead is wait - SUM(children), never wait - one-of-many (which over-reports it).
CREATE VIEW trace.blocking AS
  SELECT w.run_id,
         w.process        AS waiter,
         w.name           AS wait_span,
         w.dur_ms         AS waited_ms,
         c.blocked_on,                          -- peer process(es) doing the work
         c.work_spans,                          -- child span name(s) under this wait
         c.n_children,                          -- 1 by construction; >1 flags fan-out
         c.work_ms,                             -- SUM of the children's monotonic dur_ms
         (w.dur_ms - c.work_ms) AS overhead_ms, -- transport/queue (skew-immune: both monotonic-derived)
         w.attrs          AS wait_attrs
  FROM trace.span w
  JOIN (
        SELECT run_id, parent_span_id,
               count(*)                          AS n_children,
               sum(dur_ms)                       AS work_ms,
               string_agg(DISTINCT process, ',') AS blocked_on,
               string_agg(name, ',' ORDER BY t_start) AS work_spans
        FROM trace.span
        WHERE parent_span_id IS NOT NULL
        GROUP BY run_id, parent_span_id
       ) c
    ON c.run_id = w.run_id AND c.parent_span_id = w.span_id
  WHERE w.name LIKE '%zmq_wait%'
  ORDER BY w.run_id, w.t_start;

COMMIT;
