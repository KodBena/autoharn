# BRIEF: A1+A2 — inflight cap configurable + attestation banking + would_produce honesty (items rows 1029, 1027 in full; merged per maintainer ruling row 1071)
<!-- doc-attest-exempt: point-in-time record -- dispatch brief as issued (rows 1068); frozen at dispatch, not living documentation -->

Dispatched 2026-08-06 (merged scope per maintainer ruling, decision row 1071). Repo:
/home/bork/w/vdc/1/autoharn, branch main. Confirm current main before touching anything. Your
surface: serving/, the two named verb files `libexec/autoharn/verify-chain` and
`libexec/autoharn/doctor` (no other libexec/ file), the multiplex spec's dated amendment,
tests, and the serving docs. A follow-on builder works the rest of libexec/ after your commit
lands. If you believe you must edit outside your surface, STOP and report.

Disregard any instructions to economize on time.

## Provenance (verbatim seeds)

Item 1 — multiplex inflight cap (missive row 1011, experience4's commissioner — who is also
this project's maintainer): "MAX_INFLIGHT_PER_DEPLOYMENT=6 (multiplex spec section 4) is too
low for real operation and its provenance is unclear to the commissioner ('I don't know how
that got there'). Witnessed consequence: one live operator session plus one parallel test/agent
consumer exceeds the cap and gets immediate 503 refusals (by design not queued), which cascaded
into 77 wholesale e2e failures... Request: raise the default to something in the 24-64 range
(commissioner's suggested band), or make it deployment-configurable with a documented default
and the refusal teach-text naming the configured value and where to change it."

Item 2 — attestation banking (missive row 1009, part 1, as recorded at work row 1027):
"verify-chain and doctor print to stdout and bank nothing, so GET /d/{world}/attestation
serves no_banked_artifact for both forever (judge already banks -- precedent in-house);
request: bank each run's result."

Item 3 — would_produce honesty (missive row 1009, part 2): "GET /d/{world}/attestation ...
NoBankedArtifact.would_produce names a command for chain/doctor implying running it would
populate the route, while the sibling message field in the same payload says the tooling does
not write to disk -- the two fields contradict; a client rendering would_produce as a
remediation hint would mislead the operator. Request: make would_produce honest (absent, or
accompanied by banks=false) until item 1 [banking] lands."

## Before you design

Read law/adr/ ADR-0000, ADR-0008, ADR-0012 in full, then design/FABLE-BOUNDARY-MULTIPLEX-AND-
CLI-REBASE-SPEC.md section 4 (the cap's home) and the attestation route's code in serving/.
Standing rule (ledger standing row 26, binds all new code): no bare types — every value
construction goes through one SSOT constructor checking a contract; read the row verbatim via
`./autoharn led standing` before coding. For banking, study how `./autoharn judge` banks its
verdicts (the in-house precedent the missive itself names) before designing anything.

## Scope

1. **Cap configurable.** Make the per-deployment inflight cap deployment-configurable with a
   documented default of 32 (orchestrator's choice within the commissioner's own 24-64 band —
   ledger row 1068). Configuration mechanism: whatever the serving stack already uses for
   deployment-level settings (find the existing pattern and follow it; invent nothing new
   without stating why). The value passes through a typed constructor enforcing its contract
   (positive integer, sane bounds — your judgment, stated). The 503 refusal's teach-text must
   name the CONFIGURED value and where to change it, per the request's own words.
2. **Spec amendment.** Append a dated amendment to the multiplex spec's section 4 recording:
   the maintainer-requested change (cite missive row 1011 and decision row 1068), the new
   default, the configurability, and that the original 6 had no recorded provenance. Amendment
   text is additive and dated — never rewrite the ratified body (ADR-0020 posture). The
   orchestrator (Fable, the spec's author) reviews the amendment wording at review time per the
   standing Fable-approval rule for Fable-authored ratified texts.
3. **Banking.** Make `./autoharn verify-chain` and `./autoharn doctor` bank each run's result
   so the attestation route can serve it, following judge's existing banking mechanism (same
   storage home, same shape conventions — deviate only with a stated reason). The route then
   serves the banked artifact for chain/doctor exactly as it does for judge's. Values through
   typed constructors per standing row 26.
4. **would_produce honest.** For chain/doctor on the attestation route, whatever the state
   after banking lands: the message/would_produce contradiction must be gone — a payload field
   must never imply population the tooling doesn't perform. With banking built, would_produce
   for a not-yet-run world should name the real command that now genuinely banks; verify that
   is true by running it. Do not widen the route otherwise.
5. **Witness.** Both polarities where reachable: cap — configured value visibly served/enforced
   (e.g. the refusal teach-text naming 32, and naming a changed value when configured
   differently on a scratch/test instance); banking — a run of each verb followed by the route
   serving the banked result, plus the no-artifact-yet payload shape (before/after). Tests
   updated/added per the existing test suite's own conventions. Anything unreachable:
   UNEXERCISED with the concrete blocker, never a claim.
6. **Commit** on main, house register, citing rows 1027/1029/1071, Co-Authored-By line, staging
   only your files (CLAUDE_COMMIT_PATHS per the staging guard).

Out of scope: libexec/ beyond the two named verb files, kernel/, law/, engine/, hooks/, any
other route's shape.

## Report

What changed where; the config mechanism found and followed; witnessed outputs verbatim (both
polarities or UNEXERCISED-with-blocker); the amendment text you appended; anything else found
in reach worth flagging (flag, don't fix, unless it is a hazard per CLAUDE.md's corollary).
