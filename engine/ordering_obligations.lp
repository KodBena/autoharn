% ===========================================================================
% ordering_obligations.lp -- the closed catalogue of ordering-violations FAMILIES
% (design/ORCH-SPEC-RESOURCE-REGISTRY.md §5 stage 2), mirroring engine/preamble_obligations.lp's
% role for Part 3: one fact per family engine/lp/ordering_violations.lp's own ordering_verdict/2
% ladder ALWAYS speaks for (E8's never-silence trick, reused here) -- so an empty or pre-s22
% world still emits THREE family verdicts, never silence (the F49 vacuous-pass class ADR-0000's
% closure-statement amendment and ADR-0015 forbid). Adding or retiring a family is a facts-file
% edit HERE, never a rule rewrite in the checker itself.
%
% The three families are the residue named in ORCH-SPEC-RESOURCE-REGISTRY.md §5's own text
% ("close-before-dependency -- the verified missing check -- ... conditional-precedence ...
% and the existing cycle check re-derived") AFTER excluding what Part 3's
% engine/lp/preamble_ordering.lp already covers (F5 open-before-claim, F6 claim-before-close,
% F11's dangling-dependency member) -- see engine/lp/ordering_violations.lp's own header for the
% full non-duplication account.
% ---------------------------------------------------------------------------
ordering_family(close_before_dependency).
ordering_family(conditional_precedence).
ordering_family(dependency_cycle).
