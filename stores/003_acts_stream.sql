-- db/harness/003_acts_stream.sql
-- autoharn operational store #3 — the ACT-STREAM CONTRACT (consult 25 §2.1; Increment-4 build).
-- A vendor-NEUTRAL, append-only record of what a workflow subject actually DID, parsed post-hoc
-- from a vendor's own completed session records by a vendor-specific adapter. The independent act
-- stream the acts↔ledger differential (measurement (a)) reads: every ledgered claim should have
-- matching acts; every ledger-relevant act should have a ledger row.
--
-- SCOPE (honest): these are CLAIMS ABOUT WORK — an act stream parsed from a session's records —
-- never subject/evidence ledgers. It lives in the `harness` DB alongside the rationalization ledger
-- (db/harness/002). The subject ledger (s15) lives in a SEPARATE ISOLATED database; a subject role
-- physically cannot read this schema (catalog isolation — the e14/nla lesson).
--
-- CONTRACT vs ADAPTER (ADR-0012 P1/P2, consult 25 §2.1.2). This DDL is the vendor-NEUTRAL contract:
-- it contains ZERO vendor-isms — no "session JSONL", no "subagent", no "workflow journal". Those
-- words live ONLY in the Claude-Code adapter (tools/act_stream/claude_code_adapter.py), which is
-- vendor-specific BY CONSTRUCTION and says so. A second vendor is a second adapter over this same
-- table.
--
-- F-D LAW (consult 25 §2.1; the id-is-order discipline, byte-held from the kernel lineage):
--   `id` (ingestion order) is THE key. `vendor_seq`/`vendor_ts` are metadata that NEVER key — a
--   vendor's own sequence number or wall-clock is display/provenance only, never an ordering a
--   judgment rests on (the s12 41ms-and-same-second lesson). `payload_sha256` is ALWAYS present;
--   the raw payload stays in the committed ephemera (auditability), the excerpt is bounded for
--   adjudication legibility.
--
-- Idempotent + re-runnable, parameterized by a psql `:schema` variable (the db/harness/002 posture):
--     psql -h 192.168.122.1 -d harness -f db/harness/003_acts_stream.sql
--     psql -h 192.168.122.1 -d harness -v schema=acts_scratch -f db/harness/003_acts_stream.sql
-- Default schema: `acts`.

\if :{?schema}
\else
  \set schema acts
\endif

BEGIN;
CREATE SCHEMA IF NOT EXISTS :"schema";

-- ===== the capability manifest per stream (the ledger_edb F49 idiom, at the substrate) =====
-- A stream is one adapter run over one source. Its `manifest` declares, per fact-family, the
-- guarantee level {produced | capable | DEFERRED(reason) | EXCLUDED(reason)} — so a consumer that
-- require()s a family gets a LOUD refusal, never a silent empty read as "none exist" (F49). Live
-- hook capture is DEFERRED (mechanism 2); model-reasoning + token accounting are EXCLUDED (not acts).
CREATE TABLE IF NOT EXISTS :"schema".stream (
  id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,   -- id-is-order
  run_id     text NOT NULL,                       -- 'e15' | 'rehearsal-1' | a scratch label
  adapter    text NOT NULL,                        -- which vendor adapter produced this stream
  source_ref text NOT NULL,                        -- the completed source parsed (a dir path / commit)
  manifest   jsonb NOT NULL DEFAULT '{}'::jsonb,   -- per-family {produced|capable|DEFERRED|EXCLUDED}
  created_at timestamptz NOT NULL DEFAULT now()
);

-- ===== the kind vocabulary (CLOSED, widen-only — §2.1.1) =====
-- Defined BEFORE act (the act.kind FK references it). The plan-of-record stream is folded in as the
-- three plan_item_* kinds (a vendor without plan machinery marks that family DEFERRED in its
-- manifest — F49, absent loudly, never silently empty). WIDEN-ONLY: rows are only ever INSERTed;
-- the append-only trigger below forbids UPDATE/DELETE, so the vocabulary can grow (a new INSERT) but
-- a kind can never be narrowed away under existing acts.
CREATE TABLE IF NOT EXISTS :"schema".act_kind (
  kind text PRIMARY KEY,
  note text NOT NULL
);
INSERT INTO :"schema".act_kind (kind, note) VALUES
  ('tool_call',         'a tool invocation'),
  ('tool_result',       'the result echoed back for a tool_call'),
  ('delegation_spawn',  'a sub-agent invocation (a phase transition in a multi-agent workflow)'),
  ('delegation_return', 'a sub-agent return'),
  ('plan_item_created', 'a plan-of-record item created (native task event)'),
  ('plan_item_updated', 'a plan-of-record item state change'),
  ('plan_item_closed',  'a plan-of-record item completed/closed'),
  ('message_in',        'a message received (human/subject prompt, maintainer directive)'),
  ('message_out',       'a message surfaced by the agent (not model reasoning — that is EXCLUDED)')
ON CONFLICT (kind) DO NOTHING;

-- ===== the act (append-only; id-is-order; vendor_seq/ts NEVER key) =====
CREATE TABLE IF NOT EXISTS :"schema".act (
  id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- INGESTION ORDER — THE key (F-D)
  run_id         text NOT NULL,                    -- 'e15' | 'rehearsal-1' | ...
  stream_id      bigint NOT NULL REFERENCES :"schema".stream(id) ON DELETE CASCADE,
  vendor_seq     text,                             -- the vendor's own record id (uuid) — METADATA, never keys
  vendor_ts      timestamptz,                      -- the vendor's wall-clock — METADATA, never keys (F-D law)
  actor          text NOT NULL,                    -- 'main' | 'sub:<label>' | 'human:<who>' (from record structure)
  kind           text NOT NULL REFERENCES :"schema".act_kind(kind),  -- closed, widen-only (§2.1.1)
  name           text,                             -- tool name / agent label / plan verb
  target         text,                             -- path / db object / ledger row ref, WHEN classifiable
  payload_sha256 text NOT NULL,                    -- ALWAYS — raw payload stays in committed ephemera
  payload_excerpt text                             -- bounded, for adjudication legibility
);

CREATE INDEX IF NOT EXISTS act_stream_idx ON :"schema".act(stream_id, id);

COMMENT ON COLUMN :"schema".act.id IS
  'Ingestion order — THE key (F-D law). vendor_seq/vendor_ts are metadata that NEVER order a judgment.';
COMMENT ON COLUMN :"schema".act.payload_sha256 IS
  'Always present. The raw payload stays in the committed ephemera (auditability); this pins it.';

-- ===== append-only hardening (the rationalization_disposition idiom — consult 25 §2.1) =====
-- An act stream is EVIDENCE: "the vendor's records show the subject did THIS" is an audit fact,
-- and rewriting or deleting it would falsify the record the differential reasons over. UPDATE/DELETE/
-- TRUNCATE are refused at the write boundary for every role (the owner can DROP by hand for a scratch
-- reset; no DML path can rewrite a logged act). Streams and the kind vocabulary are append-only too.
CREATE OR REPLACE FUNCTION :"schema".acts_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'acts.% is append-only (an act stream is an audit fact): % refused for every role. Parse a fresh stream; never rewrite a logged act.', TG_TABLE_NAME, TG_OP;
END $$;

DROP TRIGGER IF EXISTS act_append_only_row ON :"schema".act;
CREATE TRIGGER act_append_only_row BEFORE UPDATE OR DELETE ON :"schema".act
  FOR EACH ROW EXECUTE FUNCTION :"schema".acts_append_only();
DROP TRIGGER IF EXISTS act_append_only_trunc ON :"schema".act;
CREATE TRIGGER act_append_only_trunc BEFORE TRUNCATE ON :"schema".act
  FOR EACH STATEMENT EXECUTE FUNCTION :"schema".acts_append_only();

DROP TRIGGER IF EXISTS stream_append_only_row ON :"schema".stream;
CREATE TRIGGER stream_append_only_row BEFORE UPDATE OR DELETE ON :"schema".stream
  FOR EACH ROW EXECUTE FUNCTION :"schema".acts_append_only();

DROP TRIGGER IF EXISTS kind_append_only_row ON :"schema".act_kind;
CREATE TRIGGER kind_append_only_row BEFORE UPDATE OR DELETE ON :"schema".act_kind
  FOR EACH ROW EXECUTE FUNCTION :"schema".acts_append_only();

COMMIT;

-- ===== honest ledger of strength =====
-- ENFORCED at write time (structural): id-is-order (identity PK); kind closed (FK to act_kind);
--   payload_sha256 NOT NULL; append-only (trigger on act/stream/act_kind — UPDATE/DELETE/TRUNCATE refused).
-- NOT ENFORCED here (adapter's job, review-only per ADR-0011 R1): that `actor` was attributed from
--   RECORD STRUCTURE not a self-declared field; that model reasoning + tokens were EXCLUDED. The adapter
--   is vendor-specific and carries those guarantees in its manifest, not this vendor-neutral contract.
