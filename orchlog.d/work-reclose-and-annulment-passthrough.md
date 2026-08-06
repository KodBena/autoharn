subject: 25677488
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

New verb: `led work reclose <slug> <resolution> [close-contract flags...]`
([design/BRIEF-B2-SUPERSEDE-RECLOSE-2026-08-06.md](../design/BRIEF-B2-SUPERSEDE-RECLOSE-2026-08-06.md),
rows 1025/1008/1200) composes a slug's current close row's supersession (s31) with a corrected close in one
guided act — the same flag vocabulary `led work close` already accepts. This is
**supersession-as-annulment**, row 1008's own name for it: a `--review-deferred` close that was
WRONG (not merely un-reviewed) gets CORRECTED, not reviewed, and the correction discharges the
very review debt the wrong close minted, because the debt's close row is no longer current.
Refuses teachably: unknown slug, no in-force close row to supersede (nothing to reclose — use
`led work close` for a first close), and a hand-supplied `--supersedes` (this verb computes the
one correct target itself, so the two can never drift apart).

**What a restarting orchestrator needs to know:** `--review-annulled <ref>` is a fourth
disposition constructor on `led work close`/`led work reclose` alike, passing through to s73's
typed `annulled` value. It is ATTEMPTED, never faked client-side — on a pre-s73 world (today's
autoharn3 included) the kernel's own `work_review_disposition_check` refuses it, surfaced
byte-verbatim; on a world born after s73, the same command is legal and discharges the debt with
no `work_review_gap` entry at all.

`hooks/stop_clean_exit.py`'s DEFERRED REVIEW OBLIGATIONS teach-text now names this supersession
path beside the pre-existing distinct-actor review path (row 1008's own finding: a real session
was steered into an attest-as-carrier misfit because only the review path was ever taught).

Full recipe with witnessed both-polarity transcripts:
[user-guide/recipes/THE-RECORD.md's "Correcting the record"
section](../user-guide/recipes/THE-RECORD.md#correcting-the-record--supersession-and-what-to-do-about-its-fallout) —
one home, not duplicated here.
