# PG-HBA-HARDENING — closing the network superuser trust hole on the toy-db host

Status: **PREPARED-UNAPPLIED.** Investigated read-only (Sonnet, 2026-07-10) against the live
cluster at `192.168.122.1`. Every fact below is WITNESSED — the actual query, the actual output.
No file on the db host was written; no role, password, or `pg_hba.conf` line was changed. Applying
any of it is the maintainer's act (`CLAUDE.md` ORCHESTRATION: "nobody edits... without a
maintainer-ratified spec" — network/credential hardening on a live evidence db is the same class of
act). This doc is that spec, written so the maintainer's part takes minutes, not an investigation.

**The irony, named out loud:** the read path used to write this document — `psql -U bork` against
`192.168.122.1`, no password, trusted by the very `pg_hba.conf` rule this doc recommends closing —
is the identical hole the run-5 incident exploited to delete a governance row. Every command below
that says "WITNESSED" ran through that open door. Closing it is the point.

---

## 1. Observed current state (WITNESSED, 2026-07-10)

### 1.1 Connection and server identity

```
$ psql -h 192.168.122.1 -U bork -d toy -c "SELECT current_user, session_user, inet_server_addr(), inet_client_addr();"
 current_user | session_user | inet_server_addr | inet_client_addr
--------------+--------------+------------------+------------------
 bork         | bork         | 192.168.122.1    | 192.168.122.68
```

No password was supplied, none was prompted for. `~/.pgpass` on this (client) host has **no entry**
for `192.168.122.1:5432:toy:bork:*` — the only entries it carries are for db `epistemic`, users
`led_s2`..`led_s9` (verified: `awk -F: '{print $1":"$2":"$3":"$4}' ~/.pgpass`, 8 lines, all
`epistemic`/`led_s*`). **This connection was not a leaked credential — it was pure trust auth.**

```
$ psql ... -c "SHOW hba_file;"
                 hba_file
------------------------------------------
 /home/bork/postgres/pgdb1/db/pg_hba.conf

$ psql ... -c "SHOW password_encryption;"
 password_encryption
---------------------
 scram-sha-256

$ psql ... -c "SHOW listen_addresses;" -c "SHOW port;" -c "SHOW ssl;"
 listen_addresses
------------------
 192.168.122.1
 port: 5432 | ssl: off

$ psql ... -c "SELECT version();"
 PostgreSQL 18.4 on x86_64-pc-linux-gnu ...
```

`password_encryption` is already `scram-sha-256` (the modern, non-MD5 hash) — nothing to change
there, the server-side default is right. `hba_file` and `data_directory`
(`/home/bork/postgres/pgdb1/db`) do **not exist on this client's filesystem** (`ls` on that path
here returns "No such file or directory") — the db runs on a **separate host**, `192.168.122.1`
(the libvirt default-NAT gateway address), reached from this guest (`192.168.122.68`) over the
subnet. **Every step below that edits `pg_hba.conf` or restarts/reloads postgres must be run ON
`192.168.122.1`, not on this machine.**

### 1.2 The rules, verbatim (`pg_read_file('pg_hba.conf')`, full file, 186 lines; the stock
PostgreSQL header comment runs lines 1–113 unmodified, first live rule at line 116)

```
114	# TYPE  DATABASE        USER            ADDRESS                 METHOD
115
116	# --- e15 subject-credential confinement (2026-07-06, BLOCKING-confine-subject-role.md fix (A)) ---
117	# First match wins: vsr_rw authenticates ONLY to vsr; every other database, any address,
118	# any socket, is rejected BEFORE the broad per-db "all"-role lines below can admit it.
119	# Any future database added to the cluster is covered by the reject lines automatically.
120	# (nla_rw is deliberately NOT confined: e14 is closed and its witness documents the
121	#  unconfined posture that actually held; rewriting it now would falsify the record's frame.)
122	host  hvn  hvn_rw  192.168.122.68/32  trust
123	host  hvn  hvn_rw  192.168.122.1/32   trust
124	host  all  hvn_rw  0.0.0.0/0          reject
125	local all  hvn_rw                     reject
126	host  hvn  all     192.168.122.68/32  trust
127	host  hvn  all     192.168.122.1/32   trust
128	########
129	host  toy  toycolors_rw  192.168.122.68/32  trust
130	host  toy  toycolors_rw  192.168.122.1/32   trust
131	host  all  toycolors_rw  0.0.0.0/0          reject
132	local all  toycolors_rw                     reject
133	host  toy  all     192.168.122.68/32  trust
134	host  toy  all     192.168.122.1/32   trust
135	########
136	host  qbx  qbx_rw  192.168.122.68/32  trust
137	host  qbx  qbx_rw  192.168.122.1/32   trust
138	host  all  qbx_rw  0.0.0.0/0          reject
139	local all  qbx_rw                     reject
140	host  qbx  all     192.168.122.68/32  trust
141	host  qbx  all     192.168.122.1/32   trust
142	########
143	host  wmb  wmb_rw  192.168.122.68/32  trust
144	host  wmb  wmb_rw  192.168.122.1/32   trust
145	host  all  wmb_rw  0.0.0.0/0          reject
146	local all  wmb_rw                     reject
147	host  wmb  all     192.168.122.68/32  trust
148	host  wmb  all     192.168.122.1/32   trust
149	########
150	host    vsr             vsr_rw          192.168.122.68/32       trust
151	host    vsr             vsr_rw          192.168.122.1/32        trust
152	host    all             vsr_rw          0.0.0.0/0               reject
153	local   all             vsr_rw                                  reject
154	# --- end confinement block ---
155
156	# "local" is for Unix domain socket connections only
157	local   all             all                                     trust
158	# IPv4 local connections:
159	host vsr all 192.168.122.68/32 trust
160	host vsr all 192.168.122.1/32 trust
161	host nla all 192.168.122.68/32 trust
162	host nla all 192.168.122.1/32 trust
163	host epistemic all 192.168.122.68/32 trust
164	host epistemic all 192.168.122.1/32 trust
165	host harness all 192.168.122.68/32 trust
166	host harness all 192.168.122.1/32 trust
167	host control_research all 192.168.122.68/32 trust
168	host control_research all 192.168.122.1/32 trust
169	host throughput_research all 192.168.122.68/32 trust
170	host throughput_research all 192.168.122.1/32 trust
171	host research all 192.168.122.68/32 trust
172	host research all 192.168.122.1/32 trust
173	host test_db all 192.168.122.68/32 trust
174	host test_db all 192.168.122.1/32 trust
175	host todo all 192.168.122.68/32 trust
176	host todo all 192.168.122.1/32 trust
177	#host    all             all             127.0.0.1/32            trust
178	# IPv6 local connections:
179	#host    all             all             ::1/128                 trust
180	#local   replication     all                                     trust
181	#host    replication     all             127.0.0.1/32            trust
182	#host    replication     all             ::1/128                 trust
```

Cross-checked mechanically against `pg_hba_file_rules` (not the raw text — the view the maintainer
should prefer, since it re-parses the live file and surfaces a syntax error per row rather than
crashing): `SELECT count(*) FROM pg_hba_file_rules` → **47 active rules**, matching the 47
non-comment lines above 1:1, zero rows with `error IS NOT NULL`.

**The shape, in one sentence:** every database in the cluster (`toy` among them) carries a `host
<db> all <addr>/32 trust` catch-all — either inside the "e15 confinement" block (lines 126–127,
133–134, 140–141, 147–148) or in the later block (lines 159–176) — that admits **any role name**,
`bork` included, with **no password**, from either of two hardcoded addresses: `192.168.122.68`
(this harness/guest host) and `192.168.122.1` (the db host itself). Line 157 (`local all all
trust`) grants the same for any Unix-socket connection on the db host, regardless of database or
role. The e15 confinement block (2026-07-06) already solved *this exact shape* for the four
per-app `_rw` roles (`hvn_rw`, `toycolors_rw`, `qbx_rw`, `wmb_rw`, `vsr_rw`) — reject-else-permit,
first match wins — but it never touched the superuser, because the superuser was not the actor e15
was written to confine.

### 1.3 Roles (`SELECT rolname, rolsuper, rolcanlogin FROM pg_roles`, 53 rows)

**Exactly one superuser role exists: `bork`** (`rolsuper=t`). No `postgres` role exists on this
cluster at all — it does not appear in the 53-row list. Every other login role (`rolsuper=f`,
`rolcanlogin=t`) is an application `_rw` role: `toycolors_rw`, `toy_rw`, `run3_rw`, `run4_rw`,
`run5_rw`, `run6_rw`, `hvn_rw`, `qbx_rw`, `qbx_rev1`, `qbx_rev2`, `vsr_rw`, `wmb_rw`, `nla_rw`,
`lab_rw`, `armvalarm_rw`, `s16val_rw`, `s18arm_rw`, `s20probe_rw`, `scratcharmarm_rw`,
`scratcharm2arm_rw`, `scratcharm3arm_rw`, `led_s2`..`led_s14` (+ `led_s13probe`, `led_s14probe`) —
plus PostgreSQL's built-in non-login `pg_*` predefined roles.

`bork` has **no password set** at all today: `SELECT rolname, rolpassword IS NOT NULL FROM
pg_authid WHERE rolname='bork'` → `f`. This matters operationally (§3, ordering) — flipping the hba
rule to `scram-sha-256` before a password exists locks the role out entirely, including from the
guard session.

### 1.4 The `toy` database's actual content (WITNESSED, confirms the incident's shape)

`toy` has 13 schemas, each a run/world (`run3`, `run3_kernel`, `run4`, `run4_kernel`, `run5`,
`run5_kernel`, `run6`, `run6_kernel`, `s20probe`, `s20probe_kernel`, `toycolors`,
`toycolors_kernel`), each with the same 6 tables (`countersign_obligation`, `ledger`,
`review_detail` / `principal`, `principal_role`, `stamp_secret`), **all owned by `bork`** (`\dt`,
`\dn`). The `_rw` roles' actual grants (`information_schema.role_table_grants` for
`run5_rw`/`run6_rw`/`toycolors_rw`) are **`SELECT`/`INSERT` only — no `UPDATE`, no `DELETE`, on any
table**, confirming the append-only design is enforced at the grant (and, per BACKLOG's run-5
forensics entry, an append-only trigger) level for the app roles. **This is exactly why the
incident required superuser**: `run5_rw` itself cannot `DELETE` a ledger row under any
circumstance; `bork`, being superuser, can bypass both the grant and the trigger. The hazard is not
"an app role can delete" (it structurally cannot) — it is "anyone on the subnet can *become*
`bork`, for free, and `bork` can do anything."

---

## 2. The minimal hardening

**One new rule block, inserted once, before every existing rule** — not a per-database patch
repeated five or nine times. `bork` is the *only* superuser and the hole has the *same shape* on
every database in the file (§1.2); patching `toy` alone would leave the identical hole open on
`hvn`/`qbx`/`wmb`/`vsr`/`nla`/`epistemic`/`harness`/`control_research`/`throughput_research`/
`research`/`test_db`/`todo` — the class, not just the run-5 instance. A single rule for role `bork`,
placed first, forecloses it everywhere in one edit (the file's own e15 precedent — reject-else,
first match wins — extended to the superuser).

**Named, explicitly:**

- **Changes:** one new block is *inserted*, before line 116 (before the e15 comment header). No
  existing line is edited, reordered, or deleted. Line numbers below 116 shift down by the number of
  inserted lines; that is expected and harmless — `pg_hba.conf` matching is order-, not
  line-number-, dependent.
- **Stays exactly as-is:** every rule in §1.2 — the e15 confinement block for `hvn_rw`/
  `toycolors_rw`/`qbx_rw`/`wmb_rw`/`vsr_rw`, every `host <db> all ... trust` catch-all, and `local
  all all trust` (line 157). In particular: `run5_rw`, `run6_rw`, and `toycolors_rw` connections are
  untouched — the new rule matches on `user_name = bork` only, so it has zero effect on any
  connection that authenticates as a different role. `./led` and every other harness path that
  connects as an app `_rw` role keeps working, unmodified, because its rule is never reached (or
  reached identically to today).
- **What is deliberately NOT touched in this pass** (named, not silently left — ADR-0013 Rule 4):
  local Unix-socket trust for `bork` (line 157) is unchanged. The task and this doc's scope is the
  *network* hole a subnet-reachable agent exploited; a local-socket restriction is a materially
  different, materially riskier change (it would need `peer`/`scram` for the socket too, affecting
  every role's local access at once, including every currently-`local ... reject`-exempted `_rw`
  role) and belongs to its own ratified decision, not bundled into this one. See §5.

**The new block** (insert verbatim, immediately after line 115's blank line and before line 116's
`# --- e15 ...` comment):

```
# --- superuser network hardening (design/PG-HBA-HARDENING.md, applied <DATE>) ---
# bork is the cluster's ONLY superuser role (rolsuper=true; verified 2026-07-10 via
# `SELECT rolname FROM pg_roles WHERE rolsuper` — see design/PG-HBA-HARDENING.md §1.3).
# Placed FIRST so it wins first-match for role bork against EVERY database, present
# and future, before any later per-db "all" trust catch-all can admit it — closing
# the class in one rule rather than patching each per-db block N times.
# Local (unix-socket) trust for bork is UNCHANGED here — see the doc's §5 limits.
host  all  bork  192.168.122.68/32  scram-sha-256
host  all  bork  192.168.122.1/32   scram-sha-256
# --- end superuser network hardening ---
```

This mirrors the file's own established convention exactly (two explicit `/32` host lines, the
same two addresses every other block already hardcodes) rather than introducing a new pattern —
consistency the file already established, not a fresh invention.

---

## 3. Exact steps, in order

**Step 0 — the lockout guard (do this FIRST, and do not skip it).** In one terminal ("Terminal A"),
connect and leave the session open for the ENTIRE remainder of this procedure:

```
$ psql -h 192.168.122.1 -U bork -d toy
```

*Success:* a `toy=#` prompt, connected under today's trust rules (§1.1). *Do not `\q` this session
until step 7 passes.* This is the classic lockout guard: PostgreSQL does not re-authenticate a
session that is already established — even if a later step locks out every NEW `bork` connection
by mistake, this session keeps working and is your way back in (to re-check `pg_hba_file_rules`,
to fix a typo, to re-issue a reload) without needing a fresh authentication.

**Step 1 — back up the file, on the db host (`192.168.122.1`), not here.**

```
$ cp /home/bork/postgres/pgdb1/db/pg_hba.conf /home/bork/postgres/pgdb1/db/pg_hba.conf.bak-$(date +%Y%m%d)
```

*Success:* the `.bak-<date>` file exists alongside the original. *Failure:* permission denied →
you are not the file's owner/db-host operator; stop, this whole procedure needs that access.
*Rollback source:* this file, for the whole procedure.

**Step 2 — set a password for `bork` while the OLD (trust) rules still govern new connections.**
In Terminal A (the guard session, still open, still trust-authenticated):

```
toy=# \password bork
Enter new password for user "bork": <maintainer types it here, not echoed>
Enter it again: <repeat>
```

Use `\password`, not `ALTER ROLE bork PASSWORD '...'` typed as a literal — the meta-command prompts
via a non-echoing read and is not written to `.psql_history` in plaintext, whereas a literal SQL
string is (and would sit in shell history if passed via `-c`). *Success:* no error; `SELECT
rolpassword IS NOT NULL FROM pg_authid WHERE rolname='bork'` now returns `t` (still from Terminal
A). **Do this before step 3** — if the hba rule is flipped to `scram-sha-256` before a password
exists, `bork` cannot authenticate via SCRAM at all (there is no verifier yet), which would lock out
even Terminal A were it to reconnect. This document intentionally contains no password.

**Step 3 — edit `pg_hba.conf` on the db host.** Insert the block from §2, verbatim, immediately
before the `# --- e15 ...` line (currently line 116; do not renumber anything else, do not remove
or reorder any existing line).

*Success:* `diff pg_hba.conf.bak-<date> pg_hba.conf` shows a pure insertion (no line above or below
the new block changed). *Failure:* a diff showing any other line touched — stop, you have edited
the wrong region; restore from the backup and retry.

**Step 4 — validate the edited file BEFORE reloading**, from Terminal A (still open, still on the
pre-edit rules — editing the file on disk does not affect already-running connections or already-
parsed rules until a reload is requested):

```
toy=# SELECT line_number, type, database, user_name, address, auth_method, error
      FROM pg_hba_file_rules
      WHERE error IS NOT NULL
         OR (user_name = '{bork}' AND auth_method = 'scram-sha-256');
```

*Success:* zero rows with `error IS NOT NULL`, and exactly two rows for `user_name={bork}`,
`auth_method=scram-sha-256`, at the lowest `line_number` in the file (i.e., before the e15 block's
line numbers). *Failure:* any row with a non-null `error` — the file has a syntax problem; fix it
(most likely a column-alignment/whitespace typo) and re-run this query before proceeding. Do NOT
reload with an `error`-carrying file.

**Step 5 — reload.** From Terminal A (no new authentication needed — this is a privileged action on
an already-open superuser session):

```
toy=# SELECT pg_reload_conf();
 pg_reload_conf
----------------
 t
```

*Success:* returns `t`. Note this returning `t` only means the reload was *requested*; it does not
by itself prove the new rules are what govern new connections — that is step 6.

**Step 6 — re-verify the ACTIVE configuration**, still from Terminal A:

```
toy=# SELECT line_number, user_name, address, auth_method FROM pg_hba_file_rules
      WHERE user_name = '{bork}' ORDER BY line_number;
```

*Success:* the two new `scram-sha-256` rows appear, at the lowest line numbers in the file, and no
`error` anywhere in the full `pg_hba_file_rules` output (re-run the step-4 query once more). This is
the artifact-level confirmation (ADR-0013 Rule 5 — verify the artifact, not the claim that step 5
"succeeded"): a `pg_reload_conf() → t` that silently kept the old rules because of a parse error
elsewhere in the file is exactly the failure mode this step exists to catch.

**Step 7 — verification (the two witnesses that define done).** Do this from a **fresh terminal on
the harness host** (`192.168.122.68`), *not* Terminal A:

**Witness A — the hole is closed:**
```
$ psql -h 192.168.122.1 -U bork -d toy
Password for user bork:
```
*Success (closed):* a password prompt appears (interactive), or — run non-interactively with no
`PGPASSWORD`/`.pgpass` entry for this host/db/user — the connection is refused with `fe_sendauth:
no password supplied` / `password authentication failed for user "bork"`. *Failure (still open):*
a `toy=#` prompt with no password requested at all — the new rule did not take effect; go back to
step 6, and do not proceed past this point until it does.

**Witness B — the working paths still work:**
```
$ ./led ...   # (or whatever the operator's normal in-world command is, in a live world using
              #  run5_rw/run6_rw/toycolors_rw — NOT bork)
```
*Success:* identical behavior to before this change — connects, authenticates trust-free exactly as
today, completes its normal work. *Failure:* any authentication error on an app-role path — this
would mean the new rule (or a typo introduced while editing) is unexpectedly matching a
non-`bork` connection; revert immediately (below) and re-diagnose before retrying.

**Only once BOTH witnesses pass**, close Terminal A (`\q`).

**Rollback (at any point, if either witness fails or Terminal A itself becomes unusable):** on the
db host, `cp pg_hba.conf.bak-<date> pg_hba.conf` (restoring the pre-edit file byte-for-byte), then
`SELECT pg_reload_conf();` — from Terminal A if it is still open, or from any other still-valid
superuser access to the box (a local `psql` over the Unix socket, `local all all trust`, still
unchanged by this whole procedure, is itself a legitimate rollback path if TCP access is ever
mis-configured into a full lockout). Re-run step 6's query to confirm the rollback took.

---

## 4. Verification summary (the two witnesses that define done)

| # | Witness | Command (from harness host, fresh session) | Pass condition |
|---|---|---|---|
| A | Superuser network hole closed | `psql -h 192.168.122.1 -U bork -d toy` | Prompts for a password, or refuses without one — never a bare prompt |
| B | Working paths intact | `./led ...` (or the operator's normal app-role path) in a live world | Behaves exactly as before — no new prompt, no new failure |

Both are required. Witness A alone (hole closed) with Witness B failing is not done — it is a
different incident (an outage). Witness B alone with Witness A failing is not done — it is the
status quo, undocumented as fixed.

---

## 5. Honest limits (named, not buried)

- **This closes trust-auth, not credential theft.** Once `bork` has a password (step 2) and the
  network rule requires SCRAM (§2), a process that can read the operator's `.pgpass` or
  `PGPASSWORD` for `192.168.122.1`/`toy`/`bork` still authenticates successfully — SCRAM verifies
  *the password*, not *who is asking for it*. **Recommendation: do NOT create a `.pgpass` entry for
  `bork` (or any other superuser role) on this host.** The maintainer's own `~/.pgpass` today has no
  such entry (§1.1) — keep it that way; typing the password interactively each time is the point,
  not friction to be optimized away.
- **An agent running AS the operator's own Unix account on the db host still gets in, unchanged.**
  Line 157 (`local all all trust`) is deliberately left untouched by this pass (§2) — any process
  with a shell on `192.168.122.1` as any local Unix user authenticates to any role, `bork` included,
  over the socket, with no password, exactly as today. This is a materially different threat
  surface (it requires OS-level access to the db host itself, not merely subnet reachability) and a
  materially larger change (it would affect every role's local access, not just `bork`'s network
  access) — named here as an open question for a future, separately-ratified pass, not silently
  left unaddressed.
- **The identical rule shape recurs on every other database in the file** (`hvn`, `qbx`, `wmb`,
  `vsr`, `nla`, `epistemic`, `harness`, `control_research`, `throughput_research`, `research`,
  `test_db`, `todo` — §1.2). Because the new rule (§2) matches on `user_name=bork` before any
  per-database rule is reached, it closes the superuser hole on **all of these at once**, not just
  `toy` — this was the reason for choosing one general rule over a `toy`-only patch. It does
  **not**, however, close the equivalent hole for a *second* superuser role should one ever be
  created — any future `CREATE ROLE ... SUPERUSER` needs its own line in this same block (or a
  `SUPERUSER` group-role match, if PostgreSQL's hba syntax is extended to support it in a later
  version) or it inherits today's trust exposure by default. Flagged so it is not rediscovered the
  hard way.
- **`ssl` is `off`** (§1.1). SCRAM does not require TLS to be secure against a passive credential
  read at rest (it never sends the password itself, even in cleartext), but a *network* password
  exchange without TLS is not protected against an active on-path adversary in the same way a
  TLS-wrapped SCRAM handshake would be. Out of this pass's scope (the task is closing trust-auth,
  not adding transport encryption) — named here as a related, not-yet-addressed hazard on the same
  connection path, for a future decision.

---

## Related

- `~/.pgpass` (this client host) — read-only, structure only (passwords redacted), during this
  investigation: 8 lines, all `192.168.122.1:5432:epistemic:led_s{2..9}:<redacted>`. No entry for
  `toy`/`bork` — corroborates §1.1's "not a leaked credential" finding.
- `gates/staging_guard.py` — this doc's own commit must declare `CLAUDE_COMMIT_PATHS` explicitly
  (see the commit that introduces this file).
- `BACKLOG.md`, "Run-5 forensics (2026-07-10...)" — the append-only trigger/grant context (§1.4)
  that explains why the incident required superuser specifically, not merely `run5_rw`.
- CLAUDE.md ORCHESTRATION and the succession rule — this doc is written at PREPARED-UNAPPLIED
  strength precisely so applying it is a short, low-judgment maintainer act, per that standing
  delegation contract.
