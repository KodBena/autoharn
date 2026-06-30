#!/usr/bin/env python
"""The two concrete domain-schema instances — proof the abstraction covers both.

  * ``doc_selection_schema`` — SINGLETON (this subproject, LIVE end-to-end): "include
    this document?" interpolating {source, domain, text_len, word_count}; preview =
    the document body in the pager; classification columns = the unsupervised model's
    suggestion ('include'/'exclude') + rationale + score; verdicts include/exclude.

  * ``coref_schema`` — BATCH (the parent coref project, DEFINED not wired): "coref
    adjudication {context}"; preview = the hook's explanation text; classification
    columns = the NLP service's knowledge-grounding rows (antecedent, anaphor,
    grounding source, confidence); verdicts coreferent/not-coreferent/uncertain.

Both are built from the ONE type system in ``schema.py``; that a singleton and a
batch schema, with different fields/preview/columns/verdicts, are expressed without
any change to the schema types is the abstraction's coverage proof (ADR-0013: the
widget is first-class and generic, not a doc-selection-only throwaway)."""

from __future__ import annotations

from schema import (AdjudicationMode, Field, PromptTemplate, Schema, TextFieldPreview,
                    Verdict, VerdictVocabulary)


# ------------------------------------------------------------------ doc-selection
# payload fields (the document's intrinsic, interpolated/previewed fields)
DOC_SOURCE = Field.text("source")
DOC_DOMAIN = Field.text("domain")
DOC_TEXT_LEN = Field.integer("text_len")
DOC_WORD_COUNT = Field.integer("word_count")
DOC_BODY = Field.text("body")
# classification columns (the unsupervised model's suggestion arriving on the bus)
DOC_SUGGESTED = Field.text("suggested")      # 'include' | 'exclude' (a verdict name)
DOC_RATIONALE = Field.text("rationale")      # e.g. "difficult coref-resolution example -> include"
DOC_SCORE = Field.number("score")

DOC_INCLUDE = Verdict("include", "use this document in the corpus")
DOC_EXCLUDE = Verdict("exclude", "drop this document from the corpus")


def doc_selection_schema() -> Schema:
    return Schema(
        key="doc-selection",
        title="Document selection",
        prompt=PromptTemplate.build(
            "Include this document in the training corpus?  source=", DOC_SOURCE,
            "  domain=", DOC_DOMAIN,
            "  length=", DOC_TEXT_LEN, " chars / ", DOC_WORD_COUNT, " words"),
        payload_fields=(DOC_SOURCE, DOC_DOMAIN, DOC_TEXT_LEN, DOC_WORD_COUNT, DOC_BODY),
        preview=TextFieldPreview(DOC_BODY, title="document body"),
        columns=(DOC_SUGGESTED, DOC_RATIONALE, DOC_SCORE),
        verdicts=VerdictVocabulary((DOC_INCLUDE, DOC_EXCLUDE)),
        mode=AdjudicationMode.SINGLETON,
        table="adj_doc_selection",
    )


# --------------------------------------------------------------- coref-adjudication
# payload fields
COREF_CONTEXT = Field.text("context")            # the surrounding text
COREF_EXPLANATION = Field.text("explanation")    # the hook's explanation text (previewed)
COREF_DOC = Field.text("doc")
# classification columns — the NLP service's knowledge-grounding rows
COREF_ANTECEDENT = Field.text("antecedent")
COREF_ANAPHOR = Field.text("anaphor")
COREF_GROUNDING = Field.text("grounding_source")
COREF_CONFIDENCE = Field.number("confidence")

COREF_YES = Verdict("coreferent", "the mentions refer to the same entity")
COREF_NO = Verdict("not-coreferent", "the mentions refer to different entities")
COREF_UNSURE = Verdict("uncertain", "insufficient evidence to decide")


def coref_schema() -> Schema:
    return Schema(
        key="coref-adjudication",
        title="Coreference adjudication",
        prompt=PromptTemplate.build("Coreference adjudication for context: ", COREF_CONTEXT),
        payload_fields=(COREF_CONTEXT, COREF_EXPLANATION, COREF_DOC),
        preview=TextFieldPreview(COREF_EXPLANATION, title="hook explanation"),
        columns=(COREF_ANTECEDENT, COREF_ANAPHOR, COREF_GROUNDING, COREF_CONFIDENCE),
        verdicts=VerdictVocabulary((COREF_YES, COREF_NO, COREF_UNSURE)),
        mode=AdjudicationMode.BATCH,
        table="adj_coref",
    )


# ------------------------------------------------------ contradiction-adjudication
# A third instance — the contradiction-detection demo's decision surface. The
# fact-mining detector's transparent rules (R-NEG / R-FUNC / R-NUM) find candidate
# contradictory claim-pairs; each pair is surfaced here for a rule/human/LLM verdict.
#
# Honest-confidence posture, made TYPE-DRIVEN (ADR-0000 / ADR-0002 / ADR-0009): an
# epistemic-state interrogator must not invent the numbers it reports. So — unlike
# COREF_CONFIDENCE above, which held a REAL NLP-model score — this schema declares NO
# Field.number ANYWHERE. A fabricated probability is therefore UNREPRESENTABLE: the
# type has no slot for one. The confidence is the rule-id + the grounding, full stop.
#
# payload fields (the finding's intrinsic, interpolated/previewed context)
CONTRA_SOURCE = Field.text("source_doc")
CONTRA_SUBJECT = Field.text("subject")          # the shared canonical subj_key
CONTRA_PREDICATE = Field.text("predicate")      # the shared pred lemma
CONTRA_EXPLANATION = Field.text("explanation")  # previewed: both sentences/spans + the rule's evidence
# classification columns (the evidence row the verdict adjudicates) — ALL TEXT (no float)
CONTRA_CLAIM_A = Field.text("claim_a")
CONTRA_CLAIM_B = Field.text("claim_b")
CONTRA_RULE = Field.text("rule")                # R-NEG | R-FUNC | R-NUM
CONTRA_GROUNDING = Field.text("grounding")      # the rule-specific evidence (allowlist entry / numbers / polarity)
CONTRA_SUGGESTED = Field.text("suggested")      # a verdict name — what RulePolicy reads

CONTRA_YES = Verdict("contradiction", "the two claims genuinely contradict")
CONTRA_NO = Verdict("not-contradiction", "the rule fired but the claims are compatible")
CONTRA_UNSURE = Verdict("uncertain", "insufficient evidence to decide")


def contradiction_schema() -> Schema:
    return Schema(
        key="contradiction-adjudication",
        title="Contradiction adjudication",
        prompt=PromptTemplate.build(
            "Are these two claims contradictory?  subject=", CONTRA_SUBJECT,
            "  predicate=", CONTRA_PREDICATE),
        payload_fields=(CONTRA_SOURCE, CONTRA_SUBJECT, CONTRA_PREDICATE, CONTRA_EXPLANATION),
        preview=TextFieldPreview(CONTRA_EXPLANATION, title="contradiction grounding"),
        columns=(CONTRA_CLAIM_A, CONTRA_CLAIM_B, CONTRA_RULE, CONTRA_GROUNDING, CONTRA_SUGGESTED),
        verdicts=VerdictVocabulary((CONTRA_YES, CONTRA_NO, CONTRA_UNSURE)),
        mode=AdjudicationMode.BATCH,
        table="contra_adjudication",   # logical key; ContraStore writes the fixed contra.* DDL
    )
