<!-- doc-attest-exempt: operator runbook, point-in-time; consumer, named: the maintainer executing the experience-world rebirth; strike when executed. -->

# MAINT-EXPERIENCE-REBIRTH-RUNBOOK — rebirthing the "experience" world as "experience2"

Prepared as a read-mostly research task (ledger row 1927 decision: rebirth, not migration —
s42's hash re-denomination closes in-place migration for any populated pre-s42 world). This
document is operator guidance only; nothing in its preparation touched Postgres beyond plain
`SELECT`s, ran teardown/birth tooling beyond `--help`/dry/read modes, or wrote to the panel
repository. Every claim below is marked **WITNESSED** (I ran or read it, output shown/quoted)
or **UNWITNESSED** (asserted from source reading only, not independently exercised).

**Old world (never touched by this runbook): schema `experience`, kernel `experience_kernel`,
role `experience_rw`, db `toy` @ `192.168.122.1`. Stays as read-only evidence — never dropped.**
**Successor world (born fresh): schema `experience2`, kernel `experience2_kernel`, role
`experience2_rw`, same db/host.**

---

## 0. The one hazard this runbook exists to prevent

`bootstrap/teardown-world.sh` **does** reach live Postgres schemas — it is not a directory-only
verb. Its drop plan (`bootstrap/teardown-world.sh:216-233`) issues `DROP SCHEMA <schema>
CASCADE`, `DROP SCHEMA <kern> CASCADE`, and `DROP ROLE <role>` against whatever `<world>`
resolves to; `--dir` is a *separate*, opt-in fourth action that only fires "only then, only that
exact path" (`teardown-world.sh:286-290`) — **WITNESSED** by reading the script in full.

Consequence for this task: **never invoke `teardown-world.sh experience ...` or
`teardown-world.sh` with `--schema experience`/`--kern experience_kernel` at any point.** The
script's own scratch-safe naming allowlist (`teardown-world.sh:168-186`) does not match
`experience` anyway (it matches `run[0-9]*`, `s[0-9]*`, `faqwit*`, `svcfx*`, `probeworld*`,
`*_scratch` only), so an attempt would additionally require `--force-non-scratch` — a second,
independent gate standing between an operator and this mistake, not a substitute for simply not
running it. **This runbook never calls `teardown-world.sh` at all.** Where old wiring needs
clearing (Step 3 below), it is done by hand-selecting specific *files* to remove/overwrite —
never a schema-dropping verb.

---

## 1. Where the successor is born: reusing the panel directory, not a fresh one

**WITNESSED** (classifier run against the live directory, see Step 5's evidence below): the
panel deployment directory `/home/bork/w/vdc/1/experience/autoharn-panel` currently classifies
`AUTOHARN_PARTIAL`, not `AUTOHARN_COMPLETE` — **this contradicts this task's premise and is the
first surprise (see the Report section at the end).** It carries `deployment.json` but no
`legacy/led` (its verbs are `led`/`judge`/`pickup` at the directory root — an older, pre-"§5
rebase" scaffold shape — design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md §2) and no
`.autoharn-world.json` sentinel (it predates that spec). `classify_destination`'s actual verdict,
witnessed live:

```
DestinationState(kind=<DestKind.AUTOHARN_PARTIAL: 'autoharn-partial'>,
                  evidence=('present: deployment.json', 'missing: sentinel, legacy/led'))
```

This does **not** block reuse: `bootstrap/new-project.sh`'s classify-destination gate only
refuses on `FOREIGN` (`new-project.sh:344-351`); `AUTOHARN_PARTIAL` and `AUTOHARN_COMPLETE` both
proceed to the ordinary `deployment.json`-exists / `--force` check
(`new-project.sh:357-361`) — and `deployment.json` already exists here, so `--force` is required.

Per design/FABLE-WORLD-CONTEXT-MIGRATION-CONSULT-2026-07-19.md §1.9 (**UNWITNESSED as ratified
policy — it is a consult, not a ratified spec, but its reasoning is sound and cited here as
guidance, not authority**): "the same project directory can simply continue, pointed at the
successor world by a new `deployment.json`" — the git tree (SPA source, docs, law/ subset,
attestations) is untouched by world succession. `bootstrap/new-project.sh` in `--new-world`
mode writes only: `deployment.json`, the `.autoharn-world.json` sentinel, `.claude/` wiring,
the nine root verb shims, and `legacy/{led,pickup,asof-export,distance-to-clean}`
(`new-project.sh:990-1024`) — it never touches `frontend/`, `backend/`, `docs/`, `SPEC.md`, or
any other panel-repo content.

**Recommendation, stated as a decision the maintainer confirms (not decided here):** rebirth
`experience2` into the SAME directory, `/home/bork/w/vdc/1/experience/autoharn-panel`, via
`--force`. This also *fixes* the PARTIAL-classification gap going forward (a fresh `--new-world`
scaffold writes both the sentinel and `legacy/led`, so post-rebirth the directory classifies
`AUTOHARN_COMPLETE` cleanly). The alternative — a brand-new sibling directory — is available but
was not what the consult's own §1.9 reasoning, or the destination-state evidence above, point
toward; if the maintainer prefers a fresh directory, replace `<dest>` below with the new path and
skip the `--force` flag.

---

## 2. Naming derivation — verified, not assumed

`bootstrap/new-project.sh --new-world <world>` derives, unless overridden explicitly by
`--schema`/`--kern`/`--role`: `schema=<world>`, `kern=<world>_kernel`, `role=<world>_rw`
(**WITNESSED** by reading `new-project.sh:219-226`, and cross-checked against
`teardown-world.sh:135-137`'s own header comment, which states it mirrors the same derivation
byte-for-byte). For `<world> = experience2`:

| fact | value |
|---|---|
| schema | `experience2` |
| kernel schema | `experience2_kernel` |
| role | `experience2_rw` |
| db / host | `toy` / `192.168.122.1` (unchanged — operator-named, never guessed, per every `bootstrap/` verb's standing discipline) |

`experience2` does **not** match `teardown-world.sh`'s scratch-safe pattern either — worth
knowing now, not only at a future teardown: any *future* teardown of `experience2` will need
`--force-non-scratch` plus the typed confirmation, same as the old `experience` name would have.

---

## 3. Step-by-step — what you type, what you should see

Every step below is either **YOUR STEP** (you run it, in your own terminal) or **ANOTHER
AGENT'S STEP** (recorded here so the sequence is visible, but not something you type).

### Step 1 — confirm the current state (YOUR STEP, read-only)

```
cd /home/bork/w/vdc/1/experience/autoharn-panel
cat deployment.json
```

**Expected output** (WITNESSED, this is what it showed when I read it):
```json
{
  "db": "toy",
  "host": "192.168.122.1",
  "kern": "experience_kernel",
  "name": "autoharn-panel",
  "role": "experience_rw",
  "schema": "experience"
}
```
This confirms you are looking at the OLD world's wiring, about to be replaced. If this file
instead already shows `schema: experience2`, the rebirth already happened — stop and
investigate before repeating any step below.

### Step 2 — decide birth vehicle: TUI vs headless fallback (YOUR STEP, decision only)

Two vehicles exist for the same underlying flow:

- **`tools/setup_tui`** — the interactive wizard, the normal operator vehicle. **Two builds are
  in flight against it right now** (worktrees under `.claude/worktrees/` in this checkout) that
  change its *presentation* — typed UI elements (Track 2.1 of
  design/FABLE-SETUP-TUI-FIELD-STRATEGY.md) and prompt-text/navigation extraction (Track 2.2) —
  **not its flow**: fork-target → birth → signed-genesis → boundary → principals/authority →
  daemons, in that order, remains the same sequence regardless of which UI build has landed by
  the time you run this. If the TUI looks different from this runbook's screen-by-screen text,
  that is expected; the underlying acts (birth, genesis signing, boundary wiring) are unchanged.
- **`bootstrap/new-project.sh` headless** — the fallback if the TUI is mid-merge or misbehaving.
  Every act the TUI performs is, underneath, a call into this script or into
  `tools/setup_tui/signed_genesis.py` (which itself drives `legacy/led`, `verify-commission`,
  and `gpg` — no second mechanism). The headless path below is complete and does not depend on
  which TUI build is current.

This runbook gives the **headless path** as the primary, witnessable sequence (it is what I
could verify against source without running the TUI live), and notes where the TUI would ask the
same question interactively.

### EXECUTION NOTE (2026-07-22, first execution) — overall shape

This runbook's first live execution (maintainer-sanctioned rebirth, autoharn ledger rows
1927/1930/1931) ran Step 3 exactly as written (headless `bootstrap/new-project.sh`, no
`--boundary-url`/`--boundary-deployment` yet), then completed the signed-genesis ceremony and
the boundary/daemon wiring via `python3 -m tools.setup_tui.app --scripted <answers> --start-at
signed-genesis` (an answers-file-driven TUI run against the already-born `experience2`, rather
than continuing the headless path by hand through Section 4's raw `gpg`/`led commission`/
`verify-commission` invocations) — this is the "TUI vehicle" Step 2 names as an alternative, used
here starting mid-flow against an existing birth, which the TUI's own screens support (`dest`
classifies non-`FRESH`, so `signed-genesis`/`boundary` proceed against it directly). Every
divergence this produced is noted at its own step below. **WITNESSED** throughout — see
`/tmp/birth-experience2.log` (Step 3's full output) and the two `--scripted` transcripts this
session captured.

### Step 3 — the birth command itself (YOUR STEP)

```
cd /home/bork/w/vdc/1/autoharn
bootstrap/new-project.sh /home/bork/w/vdc/1/experience/autoharn-panel \
    --new-world experience2 \
    --db toy --host 192.168.122.1 \
    --name autoharn-panel \
    --force
```

**What this does, per source (UNWITNESSED as a live run — not executed by this preparation
task):**
- Applies the full kernel lineage chain through **s52** (`new-project.sh:417-454` — the fixed
  `-f` list ending `s52-artifact-witness-check.sql`) into fresh schemas `experience2` /
  `experience2_kernel`, granting role `experience2_rw`.
- Seeds the per-world stamp secret and row-hash genesis seed (never rotated if already present —
  moot here, this is a fresh schema).
- Runs the full s40/s43 birth sequence: `author` principal registration (self-attributed genesis
  exception), dual standing declarations (granted role + login role), and registers `reviewer`
  (subagent), `commissioner` (human), `write-boundary` (tool) principals.
- Overwrites `deployment.json` (now pointing at `experience2`/`experience2_kernel`/
  `experience2_rw`), writes the `.autoharn-world.json` sentinel, regenerates the nine root verb
  shims (`led judge pickup audit distance-to-clean verify-commission verify-chain attest-doc
  asof-export`) and `legacy/{led,pickup,asof-export,distance-to-clean}` — all pointing at THIS
  autoharn checkout's live templates (`bootstrap/templates/*.tmpl`).
- Does **not** touch `frontend/`, `backend/`, `docs/`, `SPEC.md`, `.claude/secrets/` contents
  from the old world are overwritten (fresh stamp secret — expected and correct, a new world
  needs its own), or any other panel-repo content.

**Expected output tail** (per the script's own final echo block, `new-project.sh:1058-1069`):
```
== done ==
Next steps:
  <the exact invocation you just ran>
  cd /home/bork/w/vdc/1/experience/autoharn-panel
  claude   # then type your task as your first message -- CLAUDE.md auto-loads the
           # governance preamble (author + reviewer + commissioner principals, all
           # already registered above); nothing to paste.
```
A non-zero exit at any point (kernel apply failure, birth-sequence refusal) is `set -eu`-fatal —
the script stops at the failing statement; nothing downstream runs partially.

### EXECUTION NOTE (2026-07-22) — Step 3, live

Ran exactly as written, no deviation: `bootstrap/new-project.sh /home/bork/w/vdc/1/experience/
autoharn-panel --new-world experience2 --db toy --host 192.168.122.1 --name autoharn-panel
--force`, exit 0, `== done ==` reached (**WITNESSED**, full transcript ~950 lines, kernel applied
through s52 as predicted, 6 birth-sequence ledger rows written to `experience2`, `deployment.json`
overwritten to schema/kern/role=`experience2`/`experience2_kernel`/`experience2_rw`, `led` shim
now execs THIS checkout — confirmed by `cat led`, resolving Step 7's stale-sibling finding as a
side effect exactly as predicted there). Old-world row count re-checked immediately after: still
1753 (`SELECT count(*) FROM experience.ledger`) — untouched.

**If you use the TUI instead:** its fork-target screen will classify the destination
`AUTOHARN_PARTIAL` (Step 1's evidence) and offer the existing "partial-birth" teaching copy
(design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md §3) rather than the new FOREIGN
typed-acknowledgment path — that FOREIGN branch does not apply here, since `deployment.json`
being present is exactly what makes this PARTIAL, not FOREIGN.

### Step 4 — the signed-genesis ceremony (YOUR STEP, interactive, gpg pinentry)

This is the maintainer's own interactive act — no script performs it unattended. Per
`tools/setup_tui/signed_genesis.py` (module docstring + `keygen_operator_act`,
`signed_genesis.py:317-327`) and `keys/README.md.tmpl` precedent:

1. Designate a genesis commission (either an existing `commission`-kind row read via
   `legacy/led`, or write a fresh one: `LED_ACTOR=commissioner ./legacy/led commission "<your
   statement>"` — **note: `legacy/led`, deliberately, not the rebased `./led`** — the module
   docstring explains why: this ceremony sits before the boundary is wired (Step 5), and the
   rebased `./led` refuses without `boundary_url`/`boundary_deployment` in `deployment.json`,
   which do not exist yet at this point).
2. Generate a key, ONE fixed shape, no quiz: `gpg --quick-generate-key "<Name> <email>" ed25519
   sign 0` — **gpg's own interactive pinentry prompts for the passphrase live**, at this exact
   command, in your terminal. Nothing scripts around it.
3. Export the public half: `gpg --armor --export <fingerprint> > keys/<slug>.asc`, committed
   into `keys/` (discharging the `AWAITING-KEY` stub in `keys/README.md` —
   `signed_genesis.py:362-403`'s marker-bracketed replace).
4. Sign the designated commission's exact statement bytes:
   `printf '%s' "$STATEMENT" | gpg -u <fpr> --detach-sign --armor -o
   .claude/commission-<id>.asc -` (`signed_genesis.py:452-479` — `-u <fpr>` explicit, never
   gpg's ambient default key, closing a finding from AUTOHARN_BACKFLOW.md).
5. Run the gate: `./verify-commission --id <id> --json`.

**Expected output — the verdict field, and what it means for the commit:**
- `"verdict": "VERIFIED"` — the ceremony discharges cleanly, birth continues.
- Anything else — **HARD STOP** (ledger row 1918's genesis-gate semantics,
  `signed_genesis.py:490-499`): a `NOT_VERIFIED` (or any non-VERIFIED) verdict now **halts the
  commit** by construction (`_verify_commission_ok`, `signed_genesis.py:506-515`) — this changed
  from an earlier build where a failed verification recorded a REFUSED checklist row and
  continued (design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md §6 names this as the prior open
  question, now closed the strict way). The recorded override, if you deliberately want to
  proceed anyway, is `--accept-unverified-genesis` — an explicit, decision-time flag, never a
  silent fallback.

### EXECUTION NOTE (2026-07-22) — Step 4, live, and a real hazard found and fixed in passing

This runbook's sanction for THIS execution specifically named the **scripted-key** signed-genesis
path (a throwaway fixture keypair, honestly recorded as such — never the maintainer's own
`~/.gnupg`), run via `python3 -m tools.setup_tui.app --scripted <answers-file> --start-at
signed-genesis` against the already-born `experience2` (Step 3 above).

**A real hazard, found and fixed, not routed around (CLAUDE.md engineering-responsibility
rule):** `tools/setup_tui/screens.py`'s `screen_signed_genesis` selected the fixture-keygen path
with `is_scripted = isinstance(ui, ScriptedUi)` — but `tools/setup_tui/flow_position.py`'s
`run_screen` wraps `ui` in `NavigableUi` for EVERY screen except the final commit screen
(unconditionally, for every backend, `--scripted` included), so this `isinstance` check was
**always False** — the documented "scratch GNUPGHOME + fixture passphrase, never the operator's
own keyring" safety path for `--scripted` witnessing was dead code, for every prior `--scripted`
run of this screen, not merely an edge case this run happened to hit. Witnessed live: the first
`--scripted` attempt this session made took the "Key Name-Real (your name)" / "GNUPGHOME to use
... (blank = your default ~/.gnupg)" prompts (the operator/interactive branch's own prompt text),
not the documented "scripted/fixture keygen" ones — which would have queued a REAL
`gpg --quick-generate-key` against whatever GNUPGHOME resolved, at COMMIT time, non-interactively
(no pinentry available under `--scripted`), i.e. it would have hung or failed at commit, not
merely mislabeled a checklist row. Fixed (`tools/setup_tui/screens.py`, one line, comment
explains it in place): unwrap the `NavigableUi` via its own `_inner` attribute before the
`isinstance` check — `is_scripted = isinstance(getattr(ui, "_inner", ui), ScriptedUi)`. This is
an ordinary Python bug fix (not kernel/lineage, not law/, not engine/lp/) — no Fable-authoring or
maintainer-ratification ceremony applies (standing delegation contract's own carve-out); flagged
here loudly per the hazard rule, fixed rather than worked around, and committed alongside this
runbook (see the final commit).

With the fix in place, the re-run's genesis ceremony **WITNESSED VERIFIED**: fixture key
`AUTOHARN SETUP-TUI FIXTURE KEY -- THROWAWAY <setup-tui-fixture@example.invalid>`, fingerprint
`3D1DF9CB116E91DA4EC2418CF7E38C70541142E0`, commission row 7, `verify-commission --id 7 --json`
→ `"verdict": "VERIFIED"` (full gpg good-signature detail in the JSON body). No
`--accept-unverified-genesis` override was needed or used — the hard-stop gate was never
exercised in its refusing form this run, only in its passing form. The key is a throwaway fixture,
honestly labeled as such in `keys/README.md` and the exported `keys/*.asc` filename — never
presented as the maintainer's own signing identity.

### Step 5 — post-birth wiring: the boundary multiplex config (YOUR STEP)

Per `serving/boundary_multiplex_config.py` (module docstring + `_REQUIRED_ENTRY_KEYS`,
lines 78-81), every `[deployments.<name>]` table needs exactly five keys — `pghost`,
`pgdatabase`, `pguser`, `pgschema`, `pgkern` (all five required, no others recognized, refused
by name at config load if any is missing/extra/empty). Add this entry to whatever
`boundary-multiplex.toml` the boundary service you point the panel at actually reads:

```toml
[deployments.experience2]
pghost = "192.168.122.1"
pgdatabase = "toy"
pguser = "experience2_rw"
pgschema = "experience2"
pgkern = "experience2_kernel"
```

**Expected verification:** the boundary service's own `/meta` endpoint (per
DIRECTIVE_FROM_AUTOHARN.md §2's "self-describes over HTTP" pointer) should list `experience2`
among its served deployments once the service is (re)started against this config.
**UNWITNESSED** — I did not start or query a live boundary service against this config; verify
it live once the service is running.

### EXECUTION NOTE (2026-07-22) — Step 5, live, and a scope divergence: BOTH worlds, not one

The setup TUI's own `screen_boundary` writes exactly ONE `[deployments.<world>]` table per run
(it re-derives `boundary-multiplex.toml` wholesale from `state`, for the single world the run's
`dest`/`world` answers name) — it has no notion of "add a second deployment to an existing
multiplex config" built in. This task's mission required BOTH worlds reachable (old, read-only;
new, operative) through the panel, so after the TUI's own run wrote the `experience2`-only table
(picked port 8422), the `experience` (old world) table above was **hand-added** to the same
`boundary-multiplex.toml`, by editing the file directly (not a TUI/scaffold act) — content
identical in shape to what Step 5 already prescribed, just for the second world. The boundary
service was then restarted (`kill` the old pid, re-run `./start-daemons` — its own pidfile check
correctly detected the old pid was dead and started a fresh one) to pick up the two-deployment
config.

**WITNESSED, both deployments, live HTTP:**
```
$ curl http://127.0.0.1:8422/d/experience2/health
{"world":"experience2","service_principal":null,"capabilities":{"s22_work":true,"s41_identity":true,"s43_boundary":true,"credited_view":true}}
$ curl http://127.0.0.1:8422/d/experience/health
{"world":"experience","service_principal":null,"capabilities":{"s22_work":true,"s41_identity":false,"s43_boundary":false,"credited_view":false}}
$ curl http://127.0.0.1:8422/d/experience/meta
{"known_views":[...,"question_status","standing_decisions","work_item_current",...],"lineage_head":"s39-blocks-start","boundary_version":"1.1.0"}
$ curl "http://127.0.0.1:8422/d/experience/work/items"        # real data, 100 rows returned
$ curl "http://127.0.0.1:8422/d/experience/views/question_status" | grep 1343   # question_id 1343, answered:false
```
`experience`'s capabilities correctly report `s41_identity`/`s43_boundary`/`credited_view` as
`false` (its kernel predates s40/s41/s43/s46 — exactly the pre-s40-era lineage this runbook's own
Section 4 preamble describes) — the boundary's per-request capability detection (module docstring
line 55) degrades honestly rather than erroring. No new write path was added by the second table
entry: the boundary's generic `/d/{deployment}/write/{surface}` routes exist for any configured
deployment by construction, but the panel itself (Step 5's real consumer, see below) was wired to
call writes only against `experience2` — the old world's entry in this config is read-surface-only
in *practice*, not by a mechanism this task built.

### Step 6 — start-daemons (YOUR STEP, or delegated to the TUI's own daemon screen)

The setup TUI's daemon screen generates `<dest>/start-daemons`
(`tools/setup_tui/daemon_scaffold.py:161`, `commit_executor.py:206-222`) — a per-world script
that starts whichever daemons you selected during the wizard run (e.g. the boundary service
itself, if you choose to run one per-world rather than a shared multiplexed instance). If you
ran the headless path (Step 3) instead of the TUI, this script is **not** generated — you would
need either a TUI daemon-screen pass afterward, or to start/register the relevant daemon(s) by
hand against the multiplex config from Step 5. **UNWITNESSED** which shape applies until you
decide whether `experience2` runs behind the existing shared boundary multiplex or its own
daemon.

### EXECUTION NOTE (2026-07-22) — Step 6, live

`<dest>/start-daemons` WAS generated this run (the TUI vehicle was used for the signed-genesis +
boundary screens, so its daemon-selection machinery ran too): the boundary screen's "Start the
boundary service now (this process)?" question was answered **no**, deliberately — an in-process
`BackgroundAct` child of the wizard's own Python process was judged less robust for a process that
needs to outlive this session than the generated `start-daemons` script's own `< /dev/null`,
log-redirected, backgrounded-with-`&` shape, which the commit step then ran once itself
("best-effort", per `commit_executor.py`'s own `_daemon_script_entries` comment) — **WITNESSED**:
`bash /home/bork/w/vdc/1/experience/autoharn-panel/start-daemons` → `boundary: started (pid
75516)`, confirmed running and healthy 2s later; the immediate post-start health probe inside the
same commit read `NOT-UP` (a timing race — probed before uvicorn finished binding, not a real
failure), corrected on the re-run after Step 5's config edit (fresh pid 75596, confirmed up).
**Beyond the runbook's own Step 6 scope:** the PANEL's own backend (`backend/app.py`, a SEPARATE
process from the boundary service — see the Step 5 addendum below on the panel's actual serving
architecture) was started by hand, twice (one instance per world), also via `nohup ... &
disown` rather than a generated script — no existing scaffold verb covers "start two panel
backend instances, one per world"; this is genuinely new operational shape this task's own mission
required (both worlds visible), not something `start-daemons` was ever meant to produce. See the
Report (Section 8 addendum) for the exact commands and ports.

### Step 7 — repoint the STALE sibling checkout the panel's shims currently execute (YOUR STEP)

**WITNESSED** — the panel's `led`/`pickup` shims, as they stand today, exec an absolute path
into a *different* checkout entirely:

```
$ cat /home/bork/w/vdc/1/experience/autoharn-panel/led
#!/bin/sh
HERE="$(cd "$(dirname "$0")" && pwd)"
exec env PICKUP_DEPLOYMENT="$HERE/deployment.json" \
    /home/bork/w/vdc/1/experience/autoharn/bootstrap/templates/led.tmpl "$@"
```

**ADDENDUM (legacy-led-retirement, design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md, ledger row
1149/1150) — this section's own "which template" check is now MOOT for any checkout at or
past this addendum:** `bootstrap/templates/legacy-led.tmpl` is DELETED outright; a fresh Step-3
scaffold's `./legacy/led` is a one-line teaching refusal, never a second working template `cat
led` could show by mistake. The history above (the 2026-07-22 stale-sibling incident and its
fix) stands as written, unedited.

`/home/bork/w/vdc/1/experience/autoharn` is a **separate, stale sibling checkout** — pinned at
commit `fe70575` (2026-07-17), while the checkout you are running this runbook from (this one,
`/home/bork/w/vdc/1/autoharn`) is at `016dccb` and counting: **298 commits ahead**
(`git rev-list --count fe70575..HEAD` = 298, WITNESSED). Two consequences:

1. **Step 3's `--force` re-scaffold already fixes this**, if you run it from THIS checkout
   (`/home/bork/w/vdc/1/autoharn`, as Step 3 instructs) — `new-project.sh` writes shims pointing
   at `$EXEC_ROOT`, which (unpinned, the default) is `$AUTOHARN_ROOT` = wherever you invoked the
   script from. Re-run Step 3 from THIS checkout, not from the stale sibling, and the shim
   problem disappears as a side effect.
2. **Which template, deliberately:** at this checkout's head, `bootstrap/templates/led.tmpl` is
   the **HTTP boundary client** (rebased onto `serving/`, per its own module docstring) and
   `bootstrap/templates/legacy-led.tmpl` is the **direct-psql original**. A fresh Step-3 scaffold
   writes `./led` → `led.tmpl` (boundary client, the DIRECTIVE's mandated path) and
   `./legacy/led` → `legacy-led.tmpl` (the recovery-only original) — this is a deliberate choice
   already baked into `new-project.sh`, not something you pick per-invocation. Confirm after
   Step 3 that `cat led` in the panel dir shows `led.tmpl`, not `legacy-led.tmpl`, in its exec
   line — that is the check that the boundary-only mandate (§5 below) is actually wired, not
   merely intended.

**If you do NOT re-run Step 3 from this checkout** (e.g. you already did and are only now
noticing the stale-sibling shim), the alternative fix is to `git -C
/home/bork/w/vdc/1/experience/autoharn pull` (or repoint the shims' hardcoded path directly) —
either way, deliberately choose which template family the result execs, don't assume.

### EXECUTION NOTE (2026-07-22) — Step 7, live

Both fixes applied, belt-and-braces: Step 3's re-scaffold from THIS checkout already repointed
the panel's shims here (confirmed: `cat led` in the panel dir execs
`/home/bork/w/vdc/1/autoharn/bootstrap/templates/led.tmpl`, the HTTP boundary client, not
`legacy-led.tmpl`). The stale sibling checkout itself (`/home/bork/w/vdc/1/experience/autoharn`)
was ALSO updated per this task's explicit sanction: `git fetch origin` then `git merge --ff-only
origin/main` — **WITNESSED**, fast-forwarded `fe70575 -> 001e764` cleanly (no conflicts; a
pre-existing unrelated dirty submodule pointer, `tools/makespan-scheduler`, was left untouched,
out of scope). The sibling is now current even though nothing in the panel's live wiring depends
on it anymore.

---

### EXECUTION NOTE (2026-07-22) — how the panel SPA was actually made to work, and why

**Discovery, not assumed:** the panel's OWN backend (`backend/app.py`) does not talk to the
`serving/boundary_service.py` multiplex at all — it is a separate FastAPI process with its own
DIRECT `psycopg` connection layer (`backend/config.py`'s `PanelConfig`), resolved ONCE per
process from env/`panel.toml`/`deployment.json` at startup (env-first, file-fallback, spec
SPEC.md §1). One running backend process therefore serves exactly ONE world for its whole
lifetime — there is no per-request world switch, and the frontend (`frontend/src`) calls a single
relative `/api/...` base, with no multi-backend-URL concept in its own code. Section 4 below's
"backend goes away entirely, frontend against the boundary service's HTTP surface alone" mandate
is the FUTURE state (row 1925, explicitly out of this task's scope) — as things stand today, the
boundary multiplex (Step 5 above) and the panel's own direct-`psycopg` backend are two independent
serving paths that happen to read the same Postgres schemas; this rebirth does not merge them,
and building that merge is exactly the deletion work Section 4 assigns to the panel's own future
session, not this one.

Given that architecture, "old world read-only, new world operative, both visible" (this task's
own mission wording) is achieved the minimal honest way available WITHOUT touching that
architecture: **two backend instances, one per world, on two ports**, both serving the SAME
already-built `frontend/dist` (no frontend rebuild, no code change to `backend/` or `frontend/`
was needed or made):

```
# old world (experience) -- read-only, port 8425 -- literally backend/run-dev.sh's own existing
# env recipe, unmodified, just backgrounded and on a free port instead of the squatted 8420:
env PANEL_READONLY=1 LEDGER_PG_URI="host=192.168.122.1 dbname=toy" \
    LEDGER_SCHEMA=experience LEDGER_KERNEL_SCHEMA=experience_kernel \
    LED_BIN="$(readlink -f ./led)" PANEL_BIND=127.0.0.1 PANEL_PORT=8425 \
    venv/bin/python3 -m uvicorn app:app --app-dir backend --host 127.0.0.1 --port 8425 &

# new world (experience2) -- writable (its own led conduit), port 8430:
env LEDGER_PG_URI="host=192.168.122.1 dbname=toy" \
    LEDGER_SCHEMA=experience2 LEDGER_KERNEL_SCHEMA=experience2_kernel LEDGER_ROLE=experience2_rw \
    LED_BIN="$(readlink -f ./led)" PANEL_BIND=127.0.0.1 PANEL_PORT=8430 \
    venv/bin/python3 -m uvicorn app:app --app-dir backend --host 127.0.0.1 --port 8430 &
```

**Port 8420 note:** the documented default port (`backend/run-dev.sh`, README.md) was already
bound by an unrelated stray process (`/tmp/debug-dryrun-x4fwpkgl/...` — evidently another
session's test artifact, port squatted since before this task started) — left untouched
deliberately (a concurrent builder's process is not this task's to kill, per
`concurrent-builders-need-isolation` standing practice) rather than risk another session's work;
8425/8430 used instead and named plainly here and in the Report so the maintainer knows exactly
which URL is which.

**No panel-repo code change was needed** to reach a working SPA — `panel.toml`'s existing
`[profiles.*]` mechanism and `backend/config.py`'s existing env-first precedence already supported
exactly this shape (a named profile or discrete env vars picking the world per-process); the gap
was operational (nobody had started an instance against `experience`/`experience2` with this
task's specific ports), not a defect in the panel's own code. Per the directive addendum §5 cited
in the mission brief, "if a panel-side edit is needed... make it minimal" — none was needed this
pass, so none was made; `panel.toml`'s single stale `[profiles.autoharn]` entry (pointing at an
unrelated `autoharn1` schema, pre-existing, untouched) was left as found, out of scope for this
rebirth.

## 4. Post-birth: the boundary-only mandate (ledger row 1925, DIRECTIVE addendum §5) — ANOTHER AGENT'S STEP

**WITNESSED** — row 1927 (this session's own decision, quoted in full above the fold) states
plainly: "the birth doubles as the maintainer's setup-TUI field test... The old experience
schemas stay in Postgres as read-only evidence." Row 1925 (commission) and the panel's own
DIRECTIVE_FROM_AUTOHARN.md §5 addendum (quoted verbatim, `DIRECTIVE_FROM_AUTOHARN.md:80-119`)
bind the **panel's own future session**, not you, to:

1. **Deletion, not deprecation** of every code path in the panel repo that reaches autoharn data
   without going through the FastAPI boundary service — direct psycopg, raw `SELECT`s against
   `experience`/`experience2`, and the `led`-CLI subprocess write path.
2. **The backend goes away entirely** — the panel becomes a frontend against the boundary
   service's HTTP surface alone.
3. Filing what the panel's setup surface needs from autoharn's own world-creation API (the
   commission row 1925 opened on autoharn's side) into `AUTOHARN_BACKFLOW.md`.

These are **not your steps** — they are the panel's own orchestrator's work, sequenced
"migration precedes deletion; deletion precedes or accompanies the setup surface"
(`DIRECTIVE_FROM_AUTOHARN.md:114-117`). This rebirth (Steps 1-7 above) is the migration that
sequencing depends on; do not expect the panel-side deletion to happen automatically as a
consequence of birthing `experience2` — it is a separate commissioned act, on the panel's own
ledger, after this runbook's steps land.

---

## 5. What does NOT carry over — the migration consult's 12-class taxonomy, filled in concretely

**BACKBONE DOCUMENT, not a citation:**
[vestigial_documentation/design/FABLE-WORLD-CONTEXT-MIGRATION-CONSULT-2026-07-19.md](../vestigial_documentation/design/FABLE-WORLD-CONTEXT-MIGRATION-CONSULT-2026-07-19.md)
was commissioned (maintainer, tracker row 1494) specifically against this deployment — "It
struck me that autoharn-panel is going to need a migration path, at least to preserve context"
— and its evidence base *is* the experience world (§0.1: 1,725 rows, 13 principals, 29 standing
decisions, witnessed 2026-07-19). It is filed under `vestigial_documentation/` and is
**BANKED, non-binding** ("This is not a spec. It recommends, it reserves questions, and it
licenses nothing" — its own status line) — but its taxonomy and reasoning are what this section
follows verb-for-verb, not merely cites. Confidence levels below are the consult's own, stated
per class where it stated one.

Disposition vocabulary (consult §1's own definitions): **RE-ENACT** (a fresh typed act through
the kernel's own machinery — registration, resource declaration, work open) · **RE-ASSERT** (a
fresh decision row restating the content in full, refs citing the extract/dust row) ·
**CITE-ONLY** (never becomes an operative new-world row; stays readable, citable, in the dust
schema forever) · **NEVER** (does not cross in any form).

| # | Class | Disposition | Experience world's actual content (this task's own read-only SELECTs) |
|---|---|---|---|
| 1.1 | Identity: principal roster | **RE-ENACT** | **WITNESSED**, live query against `experience_kernel.principal`: 13 principals — `author`(model), `reviewer`(subagent), `commissioner`(human), `maintainer`(human), `bork`(human), `reviewer2`(model), `item-countersign`(subagent), `cycle-countersign`(subagent), `orchestrator`(model), `fixed-point-scout`(subagent), `fix-implementer`(subagent), `generic-consultant`(subagent), `scout-adversary`(subagent). `experience2`'s birth (Step 3) auto-registers only the scaffold's standard four (`author`/`reviewer`/`commissioner`/`write-boundary`) — the other 9 need a deliberate roster walk (consult §1.1: "not every principal crosses... each *omission* is named") deciding which of the 9 domain-specific identities (scouts, item-countersign, etc.) the SPA-against-boundary-service successor still needs, given the backend deletion mandate (§4 below) may retire whole roles (e.g. does a `scout-adversary` still have a job once there's no backend to scout?). |
| 1.2 | Standing decisions | **RE-ASSERT**, per-row re-judgment | **WITNESSED**, `led standing`: 31 rows currently in force, ids `398 399 400 401 402 403 404 405 406 407 408 409 410 411 412 413 414 416 590 610 629 724 801 883 920 922 1178 1187 1714 1729 1758`. Each needs the consult's two-part check before re-asserting: (a) still believed — a silent drop is indistinguishable from an oversight, so a drop is *named*; (b) kernel-subsumption — does `experience2`'s s52 lineage (vs. the old world's s39-era kernel) now do natively what a panel-invented rule was manually emulating. Not reproduced verbatim here (31 rows, thousands of words) — read each via the dust schema (queryable read-only forever) before drafting its fresh row. |
| 1.3 | Procedures (distinguished subclass of 1.2) | **RE-ASSERT**, rationale + rejected alternatives travel with the rule | **WITNESSED** by row id, not yet read in full by this task: **row 1729** (role-name-governance, four-step proposal/countersign/registration-gate/ledger-only-filing protocol) — the consult itself flags this as the sharpest kernel-subsumption case, since `experience2`'s native s40 registration ceremony and reserved competence machinery may already do part of what row 1729 invented by hand; reconcile, don't layer. **row 1758** (cycle-execution algorithm v3, ten-step scout/adversarial-review/decompose/implement/countersign pipeline) — this is original governance work product, not configuration; its rejected-alternative reasoning must travel with any re-assertion or the next session re-litigates ground already covered. |
| 1.4 | Open work: items, dependencies, claims | **RE-ENACT** (fresh opens), debt written off by name | **WITNESSED**, `led work list` + `distance-to-clean`, current as of this task (2026-07-22, i.e. **already stale relative to the consult's own 2026-07-19 census** — see §7 point 4 below): 5 open work items (`api-server-side-pagination-architecture-question`, `cycle-9-launch`, `fix-cain-to-s25-lineage-drift`, `panel-autoharn-lineage-mismatch-fix` — **likely MOOT after this rebirth**, its premise is `autoharn1`'s lagging schema, re-judge against `experience2`'s actual s52 lineage before reopening — `spa-professionalism-cycle-2-r2`, claimant `author`); 6 deferred-review items (`commission-select-mobile-width-fix`, `cosign-profiles-error-role-alert-fix`, `item-view-back-link-context-fix`, `panel-autoharn-profile-crash-diagnosis`, `spa-audit-cycle-7-decomposition-review`, `spa-audit-scout-7`). Per consult: items cross **unclaimed** (a claim binds a session that is gone); dependency edges re-declared only where both endpoints crossed; **debt does not cross** — a deferred-review item crosses, if it crosses, as a fresh item whose description says "closed-unreviewed in the predecessor; re-verification is part of this item's scope," or is written off by name. |
| 1.5 | Open questions | **RE-ENACT** | **WITNESSED**: rows **1343** (same-session-review-independence taxonomy question) and **1408** (ADR-0013 "who decides" scope-narrowing escalation question) — both addressed to the maintainer, both genuinely still open, neither resolved by any session per their own text. Cross as fresh `led ask`-shaped rows citing origin, or are dropped by name if the successor's context makes either moot. |
| 1.6 | Resources registry | **RE-ENACT**, reach re-witnessed | **WITNESSED**, panel `CLAUDE.md` RESOURCES section: one entry, `makespan-scheduler` (service, mandated tier, ledger row 1178, supersedes row 1150) — live-deployed background process against a shared redis instance. Per consult's own hard rule: the crossing declaration carries its `proves:` history as citation but its `reach:` as **UNWITNESSED until re-probed in experience2's own environment** — the old row's own text already warns reach claims decay even within one world ("NOW ACTUALLY DEPLOYED... corrects row:1150's not-yet-deployed caveat"), so do not assume the live process survives world succession without checking. |
| 1.7 | Competence / track record | **CITE-ONLY by default**; optionally RE-ENACT once competence-band machinery lands | Not separately queried by this task (no s41 competence-grant machinery exists yet to re-enact into); 196 reviews with verdicts and the row 399-400 conflict-of-interest RCA precedent (cited in the consult's own §1.7) remain in the dust schema, citable, never operative in `experience2` unless the maintainer answers **Q4** below yes. |
| 1.8 | Estimates and actuals | **CITE-ONLY, permanently** | Standing ruling (action-stream-is-evidentiary-basis: diagnostic-grade forever) — no number crosses as operative regardless of any other decision here. |
| 1.9 | Domain artifacts: the git tree | crosses **with the repository**, one seam owned | The panel's frontend/backend/docs/SPEC.md/law subset/attestations are untouched by Step 3 (confirmed in Section 1 above) — this is the consult's own "the same project directory can simply continue, pointed at the successor world by a new `deployment.json`" shape, which is exactly what Step 3 does. **The one seam:** every `row:N` citation baked into the panel's tree (both prompt templates, `AUTOHARN_BACKFLOW.md`, consult records) becomes a *dust citation* after Step 3 runs — documents touched after that point must disambiguate (`experience row:N`), untouched historical documents stay verbatim (ADR-0005 Rule 8). |
| 1.10 | Commissions | **NEVER** | The panel's 20 commission rows, including its founding ask, are the dust world's own charter. `experience2`'s founding act is a fresh commission — its own genesis ceremony, Step 4 above — citing the predecessor's founding commission as history, never transplanting it. |
| 1.11 | Apparatus, secrets, configuration | **NEVER** (secrets) / **RE-ENACT** (settings) | Stamp secret + chain genesis seed never cross (Step 3 regenerates fresh ones by construction — expected, correct). `apparatus.json`/governed-files/hook wiring are re-established by the scaffold with `experience2`'s own explicit flags; the dust world's settings are read as *advice*, not copied — e.g. panel standing row 410 (`doc_attestation` OFF-with-reasons, "observe mode produced 155 vendor-file false positives") is exactly the kind of configuration lesson worth a fresh §1.2 re-assertion, not a silent carry. |
| 1.12 | Refusals, violations, snags, failure record | **CITE-ONLY** | Stays in the dust schema, zero operative value, highest audit value — already-extracted *lessons* from this class are §1.2/§1.3 rows and cross through those classes; the raw failure record itself never crosses. |

---

## 6. Whether the consult's own scripted path exists — and what building it would take

The consult designs a read-only extraction verb (working name `extract-context`, §2.2) and an
ingestion ceremony (§3) to make the taxonomy above mechanical rather than hand-curated. Per
autoharn's self-application rule (CLAUDE.md, 2026-07-09: "no operator procedure ships as prose
steps + hand-pasted SQL/bash where a scripted, witnessed verb is possible"), building it is the
*preferred* route once commissioned — but **it does not exist today** (**WITNESSED**: no file,
verb, or ORCH-CAPABILITIES.md entry named `extract-context` anywhere in this checkout), and this
preparation task was explicitly barred from building it. Section 5's table above was therefore
assembled the way the consult's own §9 FAQ says a pre-verb world must: hand-run `SELECT`s
against each taxonomy class's existing view/table, by this task, this once — not a repeatable
verb.

**Per-step manual-vs-scripted status, stated plainly:**

| Step | Currently | Note |
|---|---|---|
| Extraction (reading each class out of the dust world) | **MANUAL** (this task's own SELECTs, Section 5's table) | No `extract-context` verb exists; §2.2's design (mechanical, complete-per-class, zero judgment) is not built. |
| The extract artifact (provenance block + per-item records, §2.3) | **NOT PRODUCED** | This runbook is not that artifact — it is operator guidance. A real extract would be a separate, machine-produced file if/when Q2 is answered yes. |
| Ingestion (re-asserting into `experience2`) | **MANUAL**, via ordinary `led` writes | The s40/s43 write boundary that ingestion rides is already shipped (Step 3's birth sequence uses it); what's missing is only a *batching* convenience, not new kernel machinery. |
| Ingestion's closing review (§3.3) | **MANUAL**, if the maintainer wants it (Q3) | Rides existing `led review` machinery; no new tooling needed either way. |

**Build-scope estimate for `extract-context` + the ingestion ceremony, from the consult's own
design (§2/§3) — not attempted in this pass:**

- **What it touches:** an ordinary read-only operator verb, the same class as `distance-to-clean`
  or `audit` (thin repo-root shim + a script doing the real work) — **not** kernel/lineage, **not**
  law/, **not** engine/lp/ semantics. Per the consult's own reserved-question framing (Q2,
  verbatim below): *"This is an ordinary tool build, not kernel work; Sonnet-executable under a
  spec."* No Fable-authored kernel spec or maintainer-ratification-of-a-delta ceremony is
  triggered by building it.
- **Mechanical core (§2.2):** the class queries already exist as views/verbs — `standing_decisions`
  (1.2/1.3), `question_status` open rows (1.5), the `work_item_*` views for open/claimed/deferred
  (1.4), the kernel `principal` roster (1.1), the RESOURCES rows (1.6, `kind=decision` /
  `resource:`-prefixed statements), the founding commission and chain head for the provenance
  block (2.3). No new kernel view is needed for any class in the table above — the verb is
  glue over existing reads, joined and formatted into one artifact.
- **New surface:** one script (`tools/`-hosted, by the pattern other read-only verbs use),
  one repo-root shim added to `bootstrap/new-project.sh`'s existing nine-verb loop
  (`new-project.sh:993-1002`) if it is to be scaffolded automatically into every future world —
  or it could ship un-scaffolded as an autoharn-tree-only verb the operator runs from the
  *source* checkout against a `--dest` argument, sidestepping that loop entirely; either shape is
  a design decision for whoever specs it, not decided here.
- **Sizing, qualitatively:** comparable to `distance-to-clean` (a read-composing verb over
  several existing views, ~150-250 lines witnessed for that verb's own shape) plus one
  artifact-serialization pass (JSON/Markdown, per §2.3's two-register shape) — a small-to-medium
  single-file tool build, not a multi-file/multi-boundary effort. The **ingestion ceremony**
  itself (§3) needs no new tooling at all if run by hand through existing `led register-principal`
  / `led decision` / `led work open` / `led review` calls — a *batching* script to reduce
  hand-typing error across dozens of re-assertion rows would be a second, separate,
  similarly-small convenience tool, not required for correctness.
- **Ratification path:** an ordinary Sonnet-executed build under a short implementation spec
  (no Fable-authoring or maintainer-ratification ceremony required, since it touches neither
  kernel/lineage nor law/ nor engine/lp/ — the standing delegation contract's own carve-outs).

---

## 7. The consult's reserved questions (Q1–Q6), verbatim — his to answer, not ours to paraphrase

Reproduced exactly as the consult states them (§6). Each line below states, additionally, how
that answer would change a step in this runbook, and whether the rebirth in Sections 1-4 is
blocked on it.

**Q1 — Extraction timing.** *"Shall extraction be defined as the predecessor world's own final
ledgered act (§2.1's recommended shape, buying attributed/stamped/chained provenance from
existing machinery), with the after-settlement outside read available only as a named degraded
fallback for worlds that die unexpectedly?"*
→ **Does not block birth** (Steps 1-4). If YES: extraction (Section 5/6 above) should be re-run
as a ledgered act *inside* the `experience` world before it goes fully dust — i.e., before or
immediately alongside Step 3, not after. This task's own reads (Section 5's table) were
after-the-fact outside reads (the degraded fallback shape), since `experience` is still live and
no in-world extraction act was ledgered by this task (this task made no writes anywhere).

**Q2 — The verb.** *"Shall a read-only extraction verb (§2.2) be commissioned onto the operator
surface — a scripted, witnessed alternative to hand-curated extraction — with its mechanical
scope fixed as 'complete per crossing class, zero judgment'? (This is an ordinary tool build, not
kernel work; Sonnet-executable under a spec.)"*
→ **Does not block birth.** Blocks only whether Section 6's manual-extraction shape is replaced
by a real verb before ingestion happens. Conservative default if unanswered: continue manually,
per Section 5's table, as this task did.

**Q3 — Ingestion ceremony weight.** *"Shall the ingestion disposition record require one
countersign by a distinct principal over the whole batch (§3.3), or ride uncountersigned as
ordinary attributed work? (No per-row ceremony is proposed under either answer.)"*
→ **Does not block birth.** Conservative default if unanswered: require the one batch-level
review (cheap, and matches the project's general posture of assurance-over-convenience for a
solo operator) — but this is the maintainer's call, not defaulted silently by this runbook.

**Q4 — Track record crossing.** *"When the competence-band machinery exists, shall
still-believed competences cross as fresh s41 grants with dust-citing basis (the
[FABLE-RESERVED-DESIGNS §3.4] shape), or shall track record remain CITE-ONLY permanently?"*
→ **Does not block birth**, and is moot until the competence-band machinery (FABLE-RESERVED-DESIGNS
§3.4) actually ships — `experience2`'s s52 lineage does not yet carry it. Conservative default:
CITE-ONLY, unchanged, until that machinery lands and this question is revisited.

**Q5 — Typed succession record.** *"Is prose-in-provenance (the §4.4 two-way pointers)
sufficient for world succession, or should a future kernel spec mint a typed cross-world descent
record (e.g. a deployment.json field plus a dedicated first-row kind)? This consult recommends
prose now — a typed record is additive and can be specced later without rework — but flags that a
typed field is what would let tooling (pickup, the panel SPA) render lineage mechanically."*
→ **Does not block birth.** Conservative default (the consult's own recommendation): prose now —
Section 4's honesty-surface obligations (a loud early decision row, in-band re-assertion markers)
are achievable with zero kernel work; a typed record is additive later, never blocking.

**Q6 — The panel's own succession.** *"Separately from the general discipline: when
autoharn-panel actually crosses, does the maintainer want the in-place-migration question of §0's
honest boundary (can s40+ reach the live panel at all?) investigated first, or is new-world
succession the settled route for it? This consult takes no position beyond having named the
boundary honestly."*
→ **ALREADY ANSWERED, and it is the one question that WAS load-bearing for whether this runbook's
Sections 1-4 are the right shape at all.** Ledger row 1927 (quoted in full in Section 4 above,
this same session) settles it: "experience world will be REBORN, not migrated... the maintainer's
standing conditional from this same turn (if it needs ratification and is at all large in scope,
rebirth) decides this without a further question." New-world succession is the settled route;
in-place migration is closed for `experience`. Row 1927 additionally flags, unresolved, that the
same s42 wall applies to `autoharn1` and `ent` too — routed to the maintainer as its own open
strategic question, out of this runbook's scope.

### EXECUTION NOTE (2026-07-22) — the conservative defaults, actually applied, live

This runbook's first execution applied EXACTLY the conservative defaults Q1-Q5 name, no more:
the TUI's own hydration screen ("Run hydration now?") was answered **no** — nothing from Section
5's taxonomy was re-asserted, imported, or bulk-written into `experience2`; its ledger holds only
the 6 birth-sequence rows Step 3 itself wrote (principal registrations + standing declarations)
plus the one genesis commission row from Step 4. No `extract-context` verb was built (Section 6
already says it doesn't exist; this pass didn't change that). Every re-assertion Section 5's
table lists (roster walk, the 31 standing-decision rows, the 2 open questions, the 5 open work
items, the resources registry entry) remains **entirely a maintainer-judgment follow-up**, listed
plainly in the Report's "what remains" so it is not mistaken for done.

---

## 8. Report

**Runbook:** `/home/bork/w/vdc/1/autoharn/design/MAINT-EXPERIENCE-REBIRTH-RUNBOOK.md`, this
file.

**The teardown-schema-safety answer (Section 0):** `bootstrap/teardown-world.sh` drops Postgres
schemas/roles by default — it is NOT a directory-wiring-only verb, and it does NOT have a
scratch-safe match for `experience` (would additionally need `--force-non-scratch`). This
runbook never invokes it; old-world wiring is cleared only by the `--force` overwrite in Step 3,
which touches exactly `deployment.json`/sentinel/`.claude/`/verb-shims/`legacy/`, never a schema.

**Q1-Q6 (Section 7) and the extract-context build-scope (Section 6), prominently, per the
coordinator's request:**

- **Q6 is already answered** — ledger row 1927 (this session) settles new-world succession as
  the route for `experience`; it is the one question that was actually load-bearing for whether
  this runbook's shape (Sections 1-4) is right. **Q1-Q5 do NOT block the rebirth itself** — they
  govern only how faithfully the context-carryover (Section 5) and any future ingestion (Section
  6) is done, all of which is post-birth work. Conservative defaults are stated in Section 7 for
  each; none was silently adopted without saying so.
- **`extract-context` does not exist** (WITNESSED: no such file/verb anywhere in this checkout).
  Building it, per the consult's own Q2 framing, is **an ordinary tool build — not kernel work,
  Sonnet-executable under a spec** (verbatim from the consult): a small-to-medium single-file
  read-only verb gluing together views/queries that already exist (`standing_decisions`,
  `question_status`, `work_item_*`, the principal roster, RESOURCES rows, the founding
  commission/chain head), sized comparably to the existing `distance-to-clean` verb, plus one
  artifact-serialization pass. It touches neither kernel/lineage, law/, nor engine/lp/ — no
  Fable-authoring or maintainer-ratification ceremony is triggered. Full detail: Section 6.

**Surprises found:**

1. The panel deployment directory classifies `AUTOHARN_PARTIAL`, not `AUTOHARN_COMPLETE`, under
   the current `classify_destination` (it predates both the `legacy/led` split and the sentinel
   spec) — the task brief's premise was inaccurate for this specific directory; Section 1 works
   the actual classifier output into the plan instead.
2. The panel's `led`/`pickup` shims currently exec a **stale sibling checkout** 298 commits
   behind this one (not the "294+" the task brief estimated — witnessed count is exactly 298 as
   of this checkout's head), at a hardcoded absolute path unrelated to the deployment directory
   itself — re-running Step 3 from the current checkout fixes this as a side effect, but it
   would silently persist if the maintainer instead ran birth tooling from the stale sibling.
3. `verify-commission`'s genesis-gate semantics changed recently (ledger row 1918): a
   NOT_VERIFIED signature now hard-stops the birth commit by construction, where an earlier
   build let it record a REFUSED row and continue — Step 4 documents the current (strict)
   behavior and its named override.
4. **Where the current tree disagrees with, or has moved past, the 2026-07-19 consult**
   (task point 4, evidence-backed):
   - `tools/setup_tui/destination.py` (dated 2026-07-21) postdates the consult entirely — the
     FRESH/COMPLETE/PARTIAL/FOREIGN classification driving Section 1's own reasoning did not
     exist when the consult was written; the consult's own §1.11 ("apparatus.json... re-established
     by the scaffold") is consistent with it but never named it.
   - `daemon_scaffold.py`/`start-daemons` generation (Step 6) is birth-sequence machinery that
     postdates the consult; the consult's birth-sequence citations stop at the s40/s43 ceremony.
   - The genesis hard-stop (ledger row 1918, Step 4) postdates the consult's own §6/§7 framing —
     design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md §6 (dated 2026-07-21) explicitly named the
     pre-hard-stop behavior as still-open; it is now closed, strictly.
   - The kernel lineage advanced from what the consult read (s45-era `LINEAGE_CHAIN`
     characterization, §0.1/evidence-base paragraph) to **s52** in this checkout — seven more
     deltas (s46-s52) landed since 2026-07-19; Section 5's kernel-subsumption checks (rows 1.2/1.3)
     must be run against s52, not the consult's own s45 baseline.
   - The panel's own closure debt **exploded** since the consult's 2026-07-19 census (there:
     "1 claimed work item, 2 open questions, 5 deferred-review items, total 8," §0.1) — witnessed
     live today: `review-gap: 1231 rows`, total debt **1240** (Section 5's own live read), caused
     by an intervening obligate-sweep defect documented in the panel's own rows 1790-1797 (not
     something this consult could have known in advance). This does not change Section 5's
     taxonomy-class dispositions, but it means anyone re-reading the consult's own §0.1 numbers
     as current would be materially wrong.
