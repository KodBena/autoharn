# BRIEF: wave-review remediation (review rows 1178/1176/1169; findings corpus 2026-08-06 lines)

<!-- doc-attest-exempt: point-in-time record -- dispatch brief as issued; frozen at dispatch, not living documentation -->

Dispatched 2026-08-06. Repo: /home/bork/w/vdc/1/autoharn, branch main. Step 0: confirm current
main. A hooks/ builder runs concurrently — do NOT touch hooks/. Your surface: the four files
named below, their fixtures, nothing else. CLAUDE_COMMIT_PATHS staging; fetch + ff-only before
commit.

Disregard any instructions to economize on time.

This is a FIX brief, so the defect list is the commission (fix briefs carry known flaws; review
briefs never do). Read each cited review row (`./autoharn led show <id>`) in full first.

## The fixes

1. **verify-chain fabricated-verdict banking (MAJOR, row 1178).** `libexec/autoharn/verify-chain`'s
   banking-exclusion help gate fires only when `--help` is the sole arg; `verify-chain --help
   extra-arg` banks the usage text and the attestation route serves it as a verdict. Fix:
   mirror `libexec/autoharn/doctor`'s all-args loop exactly (it is verified correct — read it).
   Witness both polarities live: `--help extra-arg` banks nothing; an ordinary run still banks.
   Also witness doctor unchanged.
2. **audit_served annotation coverage + committed fixture (MAJOR, row 1176, spec A14).** Read
   design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md §5 AND its new A14 amendment — A14 clause 3 is
   your contract: `serving/audit_served.py` gains named coverage of the `annotate_names` path
   (differential of the served `_name` fields against a direct read of the same
   `kernel.principal` join), and a committed seen-red fixture exercises the join (registered
   actor → name, unregistered/null → typed null absence) and the refusal (unsupported view →
   422 naming the supported ones). Follow both files' own conventions.
3. **setup-schema minors (row 1169).** `libexec/autoharn/setup-schema`: validate
   `SchemaProvenance.read_at` in `__post_init__` like its sibling fields (ISO-8601 UTC shape);
   correct the docstring's ADR-0012 citation P1 → P10. Witness: the verb's default and
   `--provenance` outputs byte-unchanged (diff against pre-fix capture).

Out of scope: hooks/, kernel/, bootstrap/, the led.tmpl parser consolidation (deferred by the
reviewer's own recommendation), any behavior change beyond the named fixes.

Commit citing rows 1178/1176/1169 and this brief, Co-Authored-By line.

## Report

Per fix: WITNESSED verbatim both polarities / UNEXERCISED with blocker; flags in reach.
