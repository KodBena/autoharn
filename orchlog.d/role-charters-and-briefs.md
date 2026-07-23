subject: 822c2cc
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

**New operator tools: `tools/role_charter.py` and `tools/role_brief.py` — the assembly
wiring for durable roles (commission ledger row 1663, design/FABLE-ROLE-CHARTERS-AND-
BRIEFS-SPEC.md, merged `822c2cc`, 2026-07-18).** Two halves: a **charter** is the static
half — a per-role markdown file (typically `roles/<role>/CHARTER.md`, which
`bootstrap/new-project.sh` now scaffolds as an empty directory plus a README stating the
register-before-binding rule) that binds only once REGISTERED as a `decision` ledger row
naming the role's principal, the file's repo-relative path, and a sha256 the tool computes
itself from the on-disk bytes — never caller-supplied. A **brief** is the derived half —
never authored, computed at instantiation time from the world's own views: in-force
decisions, obligation debt, open questions, claimable work, and standing (an s45 suspension
surfaces LOUDLY at the top of the brief, so an instance learns it is suspended from its own
brief rather than from its first refusal). Both tools are pure CLI-side derivation — every
read and write goes through `led` subprocess calls, never a direct psql connection.
`tools/workflow_compile.py`'s driver (the workflow-unit compiler, same day's other landing)
now resolves each dispatched phase's principal via `--role-map`, checks it against
`role_charter.py show`, and hands charter+brief as dispatch content — refusing an
uncharted principal with teaching unless `--allow-uncharted` is passed explicitly.

**A disclosed, currently-live transport asymmetry between the two tools, worth knowing
before you reach for either:** `role_charter.py`'s `DEFAULT_LED` is `"./led"` (the served
boundary) as of the legacy-led-retirement rebase. `role_brief.py`'s `DEFAULT_LED` is still
`"./legacy/led"` — NOT yet updated — because its output parsers are written against the
old direct-psql `led`'s specific text shapes (pipe-delimited `led current`, `psql -x`-style
expanded records for `led show`) and the served `led.tmpl` prints different shapes
entirely; pointing it at `./led` today would silently misparse every section as empty
rather than loudly refuse. Since legacy-led-retirement deleted `legacy-led.tmpl` outright,
`./legacy/led` now resolves to a teaching-refusal stub, so `role_brief.py`'s current
default degrades to a loud, honest refusal rather than a silent wrong answer — a
deliberate, in-source-documented choice, not a hidden bug, but still an open repair item
(pass `--led ./led` explicitly to get real output, once the served-output parsers are
written).

Where the operator-facing detail lives: `user-guide/USER-RECIPES-FAQ.md`'s "Role charters
and briefs" section has the full command grammar and a witnessed `--help` transcript for
both tools.
