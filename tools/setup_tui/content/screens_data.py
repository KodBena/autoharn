#!/usr/bin/env python3
"""tools/setup_tui/content/screens_data.py -- the DATA half of `tools/setup_tui/screens.py`'s
authored copy (design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md §3, closing the maintainer's observation
b: "file size violation; factor out the configuration content from code" / law/adr/0012's P10
"data is not code"). This module is the ONE home for `screens.py`'s longer teaching prose and
multi-sentence confirm-prompt questions -- content a contributor edits AS WRITING, not as logic.
`screens.py` references these by name and interpolates runtime values via `str.format`, never by
rebuilding prose inline (spec §3).

WHAT MOVED HERE (this build's scope, not exhaustive -- see the build report for the honest line):
the two longest narrated teaching blocks (`PARTIAL_BIRTH_TEACHING`, a partial-birth refusal that
used to thread through eleven separate `ui.say` calls one sentence-fragment at a time;
`GENESIS_GATE_HARD_STOP_TEACHING`, the six-paragraph hard-stop explanation) and the confirm-prompt
questions long enough to be judged as writing rather than a one-line label (P10's own
discriminator: "a one-line label does not trigger the rule; a paragraph does"). Short, one-line
`ui.confirm`/`ui.ask_text` prompts, and the many short, data-driven probe-status lines
(`f"  {name}: GREEN ({path})"` and similar) stay in `screens.py` -- each is computed from a live
value at the call site and is judged, by the same P10 test, as the logic's own contract (an
"error/log-diagnostic"-shaped line), not authored copy. No retroactive sweep beyond this
commission's own scope (ADR-0007's Neutral clause; law/adr/0012 P10's own "no retroactive sweep"
enforcement-surface note): the remaining interleaved copy retrofits on touch, per ADR-0004.
"""
from __future__ import annotations

# --- confirm-prompt questions long enough to be judged as writing (P10) -------------------------

CONFIRM_GOVERNED_FILES_EXTEND = (
    "Extend the governed-files pattern set beyond the default (*.py) for the other languages "
    "this project contains?"
)

CONFIRM_FOREIGN_SCAFFOLD = (
    "Scaffold into this existing content anyway? (new-project.sh will be told to accept it "
    "explicitly -- no silent merge)"
)

CONFIRM_PRINCIPALS_AUTHORITY = (
    "Constitute principals & authority now? (register identities, grant competences, assert "
    "typed relations, and register role charters -- every world already has "
    "author/reviewer/commissioner from the scaffold, so skipping leaves a complete world; "
    "propaedeutic value is the point of walking it once)"
)

CONFIRM_SIGNED_GENESIS_CEREMONY = (
    "Run the Signed genesis ceremony now? (generates a keypair, exports the public half into "
    "this world's keys/, signs the genesis commission, and verifies it against your own key -- "
    "one-time, no ongoing signing burden afterward)"
)

# --- the partial-birth refusal teaching (design/FABLE-SETUP-TUI-SPEC.md, ledger row 1790 finding
# 4/5) -- format fields: world, dest, teardown_argv (the already-joined `$ teardown-world.sh ...`
# line). Each tuple entry is one logical paragraph/note/rule, in display order.
PARTIAL_BIRTH_TEACHING: tuple[tuple[str, str], ...] = (
    ("rule", ""),
    ("refusal", "  --- REFUSED: new-project.sh's own \"already exists\" gate ---"),
    ("paragraph", "  deployment.json already exists at '{dest}' -- new-project.sh refused rather "
                  "than silently overwrite it (pass --force to replace it, which this screen "
                  "deliberately does NOT do on your behalf)."),
    ("rule", ""),
    ("paragraph", "  Likely state: a PARTIAL birth. The most common way to reach this refusal is "
                  "a prior '{world}' birth that died mid-DDL (killed, crashed, network drop) "
                  "after new-project.sh had already written deployment.json but before the "
                  "kernel lineage chain finished applying -- the world is neither cleanly born "
                  "nor cleanly absent."),
    ("rule", ""),
    ("paragraph", "  Safe next step -- teardown, NOT a --force re-birth:"),
    ("paragraph", "    $ {teardown_argv}"),
    ("paragraph", "    (teardown-world.sh will ask you to type '{world}' back to confirm -- it "
                  "is destructive and irreversible: DROP SCHEMA ... CASCADE / DROP ROLE, no "
                  "undo.)"),
    ("paragraph", "  HONEST CAVEAT: teardown-world.sh was built and witnessed against CLEANLY-"
                  "born worlds. Running it against a PARTIAL kernel chain (this situation) is "
                  "UNEXERCISED -- it is very likely to work (the same DROP SCHEMA/ROLE "
                  "statements apply regardless of how far the chain got), but it has not been "
                  "witnessed doing so. If teardown itself errors, that is new information for "
                  "the same row below, not a second dead end to solve alone."),
    ("rule", ""),
    ("paragraph", "  KNOWN DEAD END, do not attempt: `new-project.sh --force --new-world` "
                  "against this same destination. s15-schema.sql (kernel/lineage, frozen-record) "
                  "is non-idempotent under re-application -- a --force re-birth over a partial "
                  "chain hits 'no unique or exclusion constraint matching the ON CONFLICT "
                  "specification' partway through DDL, a KERNEL gap this build does not own or "
                  "patch (ledger row 1792: routed to the maintainer/Fable-spec lane, parked "
                  "pending bandwidth -- NOT this build's to fix)."),
    ("paragraph", "  --- end ---"),
)

# --- the GENESIS-GATE HARD STOP teaching (ledger row 1918, closing AUTOHARN_BACKFLOW.md finding
# 1's class) -- fully static, no runtime interpolation.
GENESIS_GATE_HARD_STOP_TEACHING: tuple[str, ...] = (
    "  GENESIS-GATE HARD STOP -- the ceremony did not verify, and the commit is halting HERE "
    "(nothing after this step ran).",
    "  WHAT FAILED: verify-commission could not confirm the genesis commission's gpg signature "
    "against the keys this world trusts (this destination's keys/).",
    "  WHY IT MATTERS: this signature is what every later record in this world's ledger anchors "
    "its provenance to -- a world born on an unverifiable genesis has a permanently unverifiable "
    "audit chain (AUTOHARN_BACKFLOW.md finding 1's class).",
    "  WHAT TO CHECK: the fingerprint pinned in keys/ (see keys/README.md) matches the key that "
    "actually signed; the GNUPGHOME/keyring used to sign is the same one whose public half was "
    "exported; the .asc signature file was not corrupted or hand-edited.",
    "  HOW TO RESUME: fix the keyring/keys/ mismatch, then re-run this tool against the SAME "
    "destination -- the commit journal resumes at this exact still-PENDING step (WPC4). If the "
    "real defect is that the WRONG KEY signed (not a keyring-side fix), resuming will not repair "
    "it: the sign step already ran and is journaled DONE, so a resumed run never re-signs -- "
    "re-sign and re-verify by hand (gpg + <dest>/verify-commission), or start a fresh birth.",
    "  OVERRIDE: re-run with --accept-unverified-genesis to proceed anyway, eyes open -- the "
    "override is recorded as its own checklist row, never silent.",
)
