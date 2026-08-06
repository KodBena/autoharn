subject: 33150e9f
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

Four maintainer-prioritized `led` changes, all CLI-presentation layer only (no kernel/serving
change):

1. **Read-projection flags** — `--recent`/`current` gain `--kind <kind>` (refused against the
   live `GET /kinds` vocabulary) and `--fields f1,f2,...` (refused on an unknown field name);
   `show` gains `--fields`; `work list` gains `--state open|closed`/`--slug <slug>`/`--fields`.
   Replaces the ad-hoc `python3 -c` filters piped through `led`'s own output that orchestrator
   sessions kept reaching for.
2. **`review-gap`'s false-clean fix.** Bare `led review-gap` used to read ONLY the actor-keyed
   `/views/review_gap`, silently empty while real work-item review debt sat in
   `/views/work_review_gap` — a hazard-class false-clean read. It now reads BOTH, every row
   labeled `gap_kind` (`"actor"` | `"work_item"`).
3. **Refuse-verdict legibility.** Every review-gap row (bare or `led work review-gap`) now
   carries `review_status` (`"never-reviewed"` | `"reviewed-not-discharging"`, the latter with
   `reviewing_verdicts` naming who/what/independence) — distinguishing a defect that was reviewed
   and refused from one nobody has looked at.
4. **`--json` surface parity.** `led --json` widened from four surfaces to six —
   `obligation_revoke` and `missive_dispose` already existed as live boundary write surfaces for
   the prose verbs; only `cmd_json`'s own allowlist was behind. WITNESSED live on this checkout:
   `led --json bogus_surface ...` refuses at the usage check (`unrecognized surface`),
   `led --json obligation_revoke <missing-file>`/`led --json missive_dispose <missing-file>` both
   now progress PAST that check into the file-read path — proof the surfaces are recognized.

WITNESSED both polarities for all four items against real scratch `--profile tracker`
deployments (`seen-red/led-read-projection-flags/`, `seen-red/led-review-gap-false-clean/`,
`seen-red/refuse-verdict-legibility/`, `seen-red/json-write-surface-parity/`). Items 1-3 also
WITNESSED live on this checkout (autoharn3) — see CLI-AND-BOUNDARY.md's own new entries for the
transcripts.

**One disclosed miss, since repaired.** This commit's own doc updates to CLI-AND-BOUNDARY.md and
REVIEW-AND-GATING.md were drafted, then REVERTED before commit — a fresh-context A:B:C
attestation on the whole file is disproportionate ceremony for two paragraph-scale clarifying
notes, and faking the attestation was refused as an option. The `docs-wave-catchup` item (this
note's own wave) is that next real pass.
