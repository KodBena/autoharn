# led's boundary-rebase coverage archaeology (relocated from led.tmpl's module docstring)

Relocated 2026-07-23 (usability review, ledger row 1180 doorway round, finding 4): this text
used to be the first ~217 lines of `bootstrap/templates/led.tmpl`'s module docstring, printed
in full by `led --help`/`led -h`/`led help` before a single word of usage. Nobody using `led`
needs to read this to run the tool — it is the rebase's own coverage inventory, kept here
verbatim (ADR-0020: content preserved, not deleted) for whoever is verifying the boundary
rebase's completeness or auditing a disclosed behavior difference from the retired direct-psql
tool. `led.tmpl`'s own docstring now carries a one-sentence description, a usage line, and the
subcommand list, with a pointer back to this file for everything below.

No prose in the relocated text below has been altered — it is copied byte-for-byte from the
docstring as it stood immediately before this relocation.

---

led -- REBASED onto the boundary service (design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-
SPEC.md §5, ratified ledger row 1631; design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md, ratified row
1652). The direct-psql original, `legacy-led.tmpl` (`./legacy/led`), was 5300+ lines covering a
larger subcommand surface than this rebase originally reached -- legacy-led-retirement (design/
FABLE-LEGACY-LED-RETIREMENT-SPEC.md, ledger row 1149/1150) closed that gap and DELETED the
original outright; `./legacy/led` is now a one-line teaching refusal. See the "SCOPE, HONESTLY
NAMED" section below for the coverage table (universe: legacy's own dispatch-token diff).

TRANSPORT: every read is a GET against `/rows/*`/`/views/*`/`/standing/principals` (paginated,
walked to completion client-side, spec's own "no server-side filter grammar" discipline); every
write is a POST against `/write/<surface>`, the kernel's own `write_verdict` passed through
byte-verbatim (spec §5: "same typed verdicts"). Exit codes follow `boundary_cli_client.py`'s own
convention (module docstring there): 0 kernel-accepted, 1 kernel-refused (byte-identical to the
legacy tool's own exit for this case), 3 boundary-refused, 4 boundary-unreachable/client error.

SCOPE, HONESTLY NAMED (what this rebase covers vs. what stays `./legacy/led`-only). Extended by
the legacy-led-retirement phase-1 pass (ledger row 1149): `led work open|claim|depends|close|
list|violations|asof`, `led decomposition-review-status`, `led briefing`, and the generic path's
client-side statement-grammar pre-flight all moved from NOT COVERED to COVERED below -- see each
item's own comment for exactly how it is served and any disclosed narrowing versus the legacy
byte-for-byte original. Phase 1B (same ledger row, coordinator narrowing corrected) closed the
remainder of the `led work *` surface -- `review-gap`/`startable`/`resolve-violation`/
`supersede-cascade`, all eleven of eleven sub-verbs now covered -- and the two remaining
statement-grammar prefixes, `actual:`/`outcome:`. design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md
Parts A+B (maintainer-ratified ledger row 1150) close the FINAL two: `led obligate revoke` now
targets the new `kernel.obligation_revoke` boundary function (kernel/lineage/
s57-obligation-revocation-event.sql), and `led artifact put|get|stat` now targets the three new
`/artifacts/*` routes (serving/boundary_service.py) -- see each item's own COVERED entry below.
The legacy-led-retirement INVENTORY pass (same ledger row 1149, run as the final round before
the deletion described in design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md): a mechanical dispatch-
token diff of legacy-led.tmpl's own `case`/`if [ "${1:-}" = ...` structure against this file
found exactly one remaining NOT-COVERED family, `led principal *` (13 sub-verbs) -- now COVERED,
closing the coverage table below to zero remaining gaps; see the SCOPE table at the end of this
docstring for the full token-by-token enumeration this pass produced.
  COVERED:
    led --recent [N] / led current [N] / led show <id>      (reads, /rows/current, /rows/{id})
    led question-status / review-gap / stamp-distinctness / standing   (reads, /views/{view})
    led --json <ledger|review|registration|obligation> <file|->        (write, verbatim payload)
    led [flags] <kind> <statement...>          the generic write path -- LED_ACTOR resolution,
        -f/-e/--supersedes/--amends/--amends-scope/--answers/--refs/--concern/--evidence/
        --confidence/--event-time, and `decision`'s own --grade, ALL carried through to the
        payload exactly as the legacy tool's own flag set names them, PLUS (legacy-led-
        retirement phase 1/1B) the SAME client-side statement-grammar pre-flight the legacy
        generic path runs before ANY write is attempted: a statement beginning `resource:`/
        `estimate:`/`actual:`/`taxon:`/`interface:`/`outcome:`/`review:`/`review-done:` (after
        leading-whitespace strip) is validated against its own closed field grammar (see
        `_GRAMMAR_CHECKERS` below, ported byte-identical refusal text from legacy-led.tmpl) --
        REFUSED, nothing written, before the payload is even built, on a malformed declaration.
        All eight of legacy's own statement-grammar prefixes are now covered -- none remain.
        SAME path (ledger row 1159, 2026-07-23 Part C completion, class-ratified fail-safe
        additive-refusal lane): a GARBAGE-STATEMENT GUARD (`_cli_usage_guard_violation` below)
        refuses a statement pattern-matching CAPTURED CLI usage/help output -- a bare `--help`
        token, a `usage:` line, or a run of 3+ option-flag-shaped tokens -- the maintainer's own
        testimony that fumbled agent invocations have written CLI usage text into the ledger as
        permanent, unretractable rows. `--statement-really-contains-cli-text` overrides,
        honestly named. Runs ONLY on this generic path -- `led review`/`led work *` build their
        statements from typed fields, never raw captured terminal text.
    led register-principal <name> <class>      (write, registration_write; DISCLOSED MINOR
        DIVERGENCE, row 1173 round-2 faithfulness re-check, grammar axis verdict, no behavior
        change: a malformed invocation (missing <class>, an unrecognized flag) exits 4 here
        (this file's own argparse-SystemExit convention, `boundary_cli_client.py`'s documented
        "3 boundary-refused, 4 boundary-unreachable/client error" scheme) where legacy exits 1
        for the same bad-argument shape -- an accepted, disclosed CLI-convention difference
        of the served rebase generally, not special-cased to this one verb, and not a
        silent-vs-taught difference (both refuse, both teach; only the exit code differs))
    led obligate <scope> <assigned-by> <obliged-actor>                 (write, obligation_write)
    led review <entry-id> <verdict> <independence> [--antecedent id] <statement...>  (write)
    led decomposition-review-status     (read-only; mode from <world-root>/.claude/apparatus.json,
        countersign_obligation total/undischarged counts via /views/countersign_obligation +
        /views/review_gap walked client-side, one-line verdict -- byte-identical logic to
        legacy's own SQL, just counted in Python over the same two served views instead of one
        SQL COUNT/FILTER)
    led briefing        (read-only, no DB access at all -- ported verbatim, including the
        <world-root>/.claude/apparatus.json mechanisms.rules_briefing.extra_items extension point)
    led work open <slug> <title...> [--parent p] [--discharge composite] [--refs r]
        [--supersedes id]                     (write, kind=work_opened via /write/ledger)
    led work claim <slug>                     (write, kind=work_claimed via /write/ledger)
    led work depends <slug> <on-slug> [--type ...] [--supersedes id]
                                               (write, kind=work_depends_on via /write/ledger;
        --supersedes's own pre-write validation -- target exists/is a work_depends_on row/not
        already superseded -- reads GET /rows/{id} plus a walk of /rows/current for the
        "already superseded" check; DISCLOSED NARROWING versus legacy's raw-ledger SQL: a
        target that was itself LATER superseded by a row that is in turn ALSO superseded would
        not be found "already superseded" by this walk of CURRENT rows alone -- a rare double-
        supersession chain the kernel's own s31 trigger still catches authoritatively at
        construction either way; this client-side check is teaching, not the enforcement)
    led work close <slug> <resolution> (--review-witness r | --review-deferred |
        --review-bookkeeping --witness commit:sha) [--witness r] [--strict] [--supersedes id]
                                               (write, kind=work_closed via /write/ledger; the
        led-side claim-before-close gate reads GET /views/work_item_current for <slug>'s own
        `claimant` field rather than a raw kind=work_claimed existence scan -- same true/false
        answer for the ordinary case, a disclosed representation change, not a narrowing)
    led work list [--all]      (read, /views/work_item_current walked and filtered client-side
        to state<>'closed' by default -- --all lifts the filter; one JSON row per line, same
        convention `question-status`/etc. already use, NOT legacy's joined-claimant-name/
        effective_state_if_diff psql table -- DISCLOSED NARROWING: `claimant` prints as the
        raw principal id, never resolved to a name, and no derived effective_state_if_diff
        column is computed -- see /work verbs NOT covered below for the sub-verb this
        column's own documentation lives under)
    led work violations        (read, /views/work_item_violations walked, one JSON row per
        line -- whatever columns THIS world's kernel actually carries on the view print
        through as-is, so a pre-s37 world naturally gets the 3-column shape and a s37+ world
        gets target_id too, with no client-side version branching needed at all)
    led work asof <iso-8601 timestamp>        (read; DISCLOSED PARTIAL PORT, not byte-identical
        to legacy -- see cmd_work_asof's own docstring: reuses GET /rows/asof/{ts} -- the SAME
        supersession-filtered reconstruction `asof-export.tmpl` already serves over HTTP --
        filtered client-side to kind in work_opened/work_claimed/work_closed and reduced to
        one row per slug exactly as legacy's own three CTEs do. The ONE semantic divergence,
        disclosed rather than silently carried: legacy's raw event-replay does NOT consult
        `supersedes` at all, so a work_opened row later retracted (s31) still shows as
        permanently "open" in legacy's own asof view; this port's supersession-aware source
        route correctly drops it once its own retraction lands at-or-before the same
        timestamp. Timestamp grammar is also STRICTER (ISO-8601 only, matching /rows/asof/{ts}
        itself) than legacy's looser postgres-timestamptz-cast acceptance.
    led work review-gap        (read, /views/work_review_gap, already in VIEW_REGISTRY)
    led work startable         (read, /views/work_startable -- ADDED to VIEW_REGISTRY this
        pass, phase 1B, per the s56-views precedent, keyed on slug/slug; a pre-s39 kernel's
        404 is translated to legacy's own teach-text)
    led work resolve-violation <target-id> <reissued|retired> "<basis>"
        (--review-witness r | --review-deferred) [--witness r] [--supersedes id] [--class name]
                                               (write, kind=work_violation_disposition via
        /write/ledger; class re-derivation reads /views/work_item_violations (ordinary path)
        or GET /rows/current for the named row (--supersedes correction path) -- same
        ambiguity-refusal/mismatch-refusal teach-text as legacy)
    led work supersede-cascade <old-slug> <new-slug> <title...>
        [--parent p] [--discharge composite] [--refs r]
                                               (a CLI COMPOSITION of `work open --supersedes`
        and `work resolve-violation`, reading /views/work_edge_parent -- ADDED to VIEW_REGISTRY
        this pass, keyed on child_slug/slug, per the s56-views precedent -- plus
        /views/work_item_current and /views/work_item_violations for the per-child walk.
        DISCLOSED IMPLEMENTATION-SHAPE DIFFERENCE, not a semantic one: legacy re-execs
        `./led work open ...`/`./led work resolve-violation ...` as fresh subprocesses; this
        port calls the equivalent Python functions in-process, re-deriving each step's written
        row id via GET /rows/current exactly as legacy's own recursive shell-outs do)
    led obligate revoke <scope> --reason "<text>"   (write, kind=obligation_revoked via
        /write/obligation_revoke -- design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part A,
        kernel/lineage/s57-obligation-revocation-event.sql: the raw DELETE this verb used to
        issue is retired; revocation is now a typed, journaled ledger event, and the obligation
        row itself is never deleted -- "in force" is a derivation review_gap itself now makes.
        DISCLOSED GRAMMAR ADDITION, not silently unchanged: `--reason` is a NEW, MANDATORY flag
        -- the raw DELETE this replaces carried no reasoning at all, and the kernel function's
        own contract requires a non-empty `reason` (ADR-0013: a revocation is a maintainer act,
        and its stated ground is part of the record). `<scope>` alone, with no `--reason`, is
        REFUSED at the CLI with teach-text before any write is attempted -- the positional
        argument itself is unchanged from the legacy grammar.)
    led artifact put <path> [--media-type ...] | get <hash> [--out <path>] | stat <hash>
                                               (write/read, design/FABLE-LEGACY-LED-RETIREMENT-
        SPEC.md Part B: three new routes, POST /artifacts, GET /artifacts/{hash},
        GET /artifacts/{hash}/stat -- unchanged CLI grammar from legacy-led.tmpl's own `led
        artifact` verb. `get` re-verifies the received bytes against the requested hash
        CLIENT-SIDE too (belt-and-braces with the boundary's own server-side re-verification on
        the way out -- see serving/boundary_service.py's `artifact_get` docstring), preserving
        the legacy tool's own WA6 corruption-drill teach-text byte-for-byte.)
    led principal declare-standing|undeclare-standing|suspend|lift-suspension|revoke|relate|
        unrelate|bind-role|release-role|bind-key|revoke-key|grant-competence|withdraw-competence
                                               (write, all 13 via /write/ledger -- the legacy-
        led-retirement INVENTORY pass, ledger row 1149: an exhaustive dispatch-token diff of
        `bootstrap/templates/legacy-led.tmpl` against this file found exactly ONE uncovered
        family, `led principal *` -- never wired into this rebase's `main()` at all before this
        pass. Ported off legacy's own shared `_principal_binding_insert` shape (see the typed
        payload classes and `_write_principal` below, one writer/many callers, ADR-0012 P1;
        row 1173 finding 4 replaced the original single bag-of-optionals `_principal_write` with
        six typed dataclasses, one per write shape); duplicate-active and
        value-continuity guards read GET /rows/current client-side filtered by kind (mirrors
        `_current_row` below `cmd_work_startable`), never a raw SQL lookup. s41/s45 gating is a
        NEW client-side capability probe, GET /health's `capabilities` dict, extended this same
        pass with `s45_standing_lifecycle` (boundary_models.py's `CapabilityManifest`) --
        bespoke teach-text on both gates, byte-similar to legacy's own `has_s41`/
        `has_s45_standing_lifecycle()` refusal text. principal_relations/principal_role_bindings/
        principal_keys/principal_competences also joined VIEW_REGISTRY this pass (serving/
        boundary_service.py) as a fourth additive read-surface growth, though this dispatch
        itself reads duplicate-active state off /rows/current rather than those four views (both
        answer the same question; /rows/current needed no new registry entry to answer it, and
        avoids a SECOND capability-detection path for the very same s41 fact this section already
        gates on via /health). DISCLOSED NARROWING: an s40-only-not-yet-s41 kernel gets this
        file's own generic-shaped bespoke refusal (same wording as legacy) for the 8 s41 verbs;
        the 5 standing-lifecycle verbs (declare-standing/undeclare-standing/suspend/
        lift-suspension/revoke) need only s40 and work on such a kernel exactly as legacy does.
        DISCLOSED IMPROVEMENT, not a narrowing (row 1173 round-2 faithfulness re-check, SEVERE):
        a recognized flag given with a MISSING or EMPTY value (e.g. `--db-role` as the trailing
        token) is REFUSED here (`_parse_principal_flags`/`_parse_principal_flags_strict`'s own
        `flag '<tok>' requires a non-empty value` teach-text) -- legacy's own behavior on the
        identical input was an accidental `shift 2`-past-end crash under `set -euo pipefail`
        (exit 1, nothing written, no teach-text); this closes a REAL defect the crash used to
        mask (`declare-standing`/`undeclare-standing`'s own `db_role = flags.get(...) or
        cfg.record.role` fallback silently wrote a real standing row for the DEFAULT role, not a
        refusal) with the SAME observable contract legacy's crash had -- nonzero exit, zero
        writes -- plus teaching where legacy had a bare stack trace.)
  SCOPE, THE COVERAGE TABLE (legacy dispatch token -> served status; the universe below is every
  token `bootstrap/templates/legacy-led.tmpl` dispatches on ITS OWN top-level `if [ "${1:-}" = ...`
  chain plus every named sub-verb `case` inside it -- mechanically enumerated, ledger row 1149's
  inventory pass, not reconstructed from prose):
    --recent, current, --json, show                              COVERED
    question-status, review-gap, stamp-distinctness, standing     COVERED
    register-principal                                            COVERED
    principal (13 sub-verbs: declare-standing, undeclare-standing,
      suspend, lift-suspension, revoke, relate, unrelate,
      bind-role, release-role, bind-key, revoke-key,
      grant-competence, withdraw-competence)                       COVERED (this pass -- was the
                                                                     only NOT-COVERED family)
    obligate, obligate revoke                                      COVERED
    artifact put|get|stat                                          COVERED
    decomposition-review-status, briefing                          COVERED
    review                                                         COVERED
    work open|claim|depends|close|list|violations|asof|review-gap|
      resolve-violation|supersede-cascade|startable (11/11)         COVERED
    generic <kind> <statement...> (every kind; 8/8 statement-
      grammar prefixes: resource:/estimate:/actual:/taxon:/
      interface:/outcome:/review:/review-done:)                    COVERED
  NOT COVERED / STRUCTURALLY UNPORTABLE: NONE. Every token the mechanical dispatch-diff found is
    now COVERED (as of this inventory pass, ledger row 1149, on top of design/FABLE-LEGACY-LED-
    RETIREMENT-SPEC.md Parts A+B, ledger row 1150). The disclosed READ-SHAPE/behavior divergences
    named throughout this section above (JSON-per-line listing for `led work list`/`--json`
    views; the supersession-aware `led work asof`; the s41/s45-gated bespoke-vs-generic refusal
    text split on `led principal *`) remain the only documented behavior differences from
    `./legacy/led`.

<!-- doc-attest-exempt: mechanical relocation, ledger row 1180 usability doorway round -- this
     file's body is a byte-for-byte copy of text that already existed (bootstrap/templates/
     led.tmpl's own module docstring before this pass), moved here rather than deleted per
     ADR-0020; no prose was authored or altered by this move. Removal condition: strike this
     marker and run the real A:B:C loop the next time this file is touched for content, not
     just further relocation. -->
