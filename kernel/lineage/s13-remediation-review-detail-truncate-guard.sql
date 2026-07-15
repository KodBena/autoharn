-- Inc5 finding-6 remainder remediation (2026-07-07). s13.review_detail carried NO append-only/
-- TRUNCATE triggers while vsr.public.review_detail carries both; review_detail is append-only
-- attestation evidence (countersign_obligation is mutable config in both, correctly unguarded).
-- Applied live to epistemic.s13; committed here for auditability. Mirrors the vsr guards.
CREATE TRIGGER review_detail_append_only BEFORE DELETE OR UPDATE ON s13.review_detail
  FOR EACH ROW EXECUTE FUNCTION s13.append_only();
CREATE TRIGGER review_detail_append_only_trunc BEFORE TRUNCATE ON s13.review_detail
  FOR EACH STATEMENT EXECUTE FUNCTION s13.append_only();
