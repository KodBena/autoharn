subject: cac001e
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

`serving/` landed (`0f7e893` spec, `69e2647` first build, `d21f175`/`cac001e` A2 hardening): a
FastAPI service is now the one declared **Port** (ADR-0012 P2) into an autoharn-managed ledger
for UI-class and programmatic consumers — the autoharn-panel Vue SPA first, but nothing stops a
future orchestrator session from talking to a world through it instead of shelling out to `led`.
Full spec: [design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md](../design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md)
(read Amendments A1 and A2 too — A2 is the hardening basis, seven adjudicated post-build
findings); operator pointer: [serving/README.md](../serving/README.md).

**Not a kernel-lineage delta — no birth-chain gate applies.** Unlike the s-numbered deltas this
directory usually logs, `serving/` is ordinary application code that ships in this checkout and
runs against whatever world's `deployment.json` you point it at. Capability is DETECTED per
request (object existence via `to_regclass`/`pg_proc`, never a version literal) rather than
gated by which commit scaffolded the world — a world that predates s40/s41/s43 still gets a
working `/health`, `/rows/current`, and `/work/items` from this service; only the endpoints that
need a capability that world lacks refuse with a typed `capability_absent`. WITNESSED against
`autoharn1` (a world with `s22` work but no `s41`/`s43`):
```
GET /health -> {"world":"autoharn1","service_principal":null,
  "capabilities":{"s22_work":true,"s41_identity":false,"s43_boundary":false,"credited_view":false}}
```

**The write endpoints are the one thing to internalize before pointing a session at this.** Four
routes, one per s43 [write boundary](../GLOSSARY.md#write-boundary) function
(`/write/ledger`, `/write/review`, `/write/registration`, `/write/obligation`). A kernel refusal
comes back as **HTTP 200** carrying the kernel's own [typed verdict](../GLOSSARY.md#typed-verdict)
verbatim — do not read a 200 as "the write happened," check `disposition`. On a pre-s43 world
every write endpoint refuses entirely (`capability_absent`, HTTP 409) rather than falling back to
a raw `INSERT` — there is no DML string anywhere in `serving/`, grep-provable. WITNESSED against
`autoharn1`:
```
POST /write/ledger -> HTTP 409 {"disposition":"capability_absent","capability":"s43-boundary", ...}
```

**Attribution is honestly limited, not silently assumed.** The service does not itself inject an
`actor` on a caller's behalf — it passes through whatever the caller supplied, or lets the
kernel's own `set_actor` default apply exactly as an unset `LED_ACTOR` does for `led`. A
deployment that wants service-originated writes attributed to a dedicated `boundary-service`
principal has to provision a distinct login role and standing declaration for it (README's
"The write path" section has the ceremony); until that's done, treat writes through the service
as attributed the same as an anonymous `led` write on the connecting role.

**Bind guard, size bound, and the audit verb, briefly (full detail in the spec/README):**
loopback-only unless `--i-understand-this-exposes-the-ledger` is passed; write bodies over 1 MiB
refuse HTTP 413 at two checkpoints (before JSON parsing, before the subprocess); FastAPI's own
`/docs`/`/redoc`/`/openapi.json` are disabled outright, not merely unlisted (A2.1 — the
pre-hardening build's route claim was FALSE against the running service, caught by independent
review); `serving/audit_served.py` ships WITH the service and does a live served-vs-kernel spot
differential (`AGREE`/exit 1 on a real mismatch/exit 2 on a transport failure) — treat it the
same way you'd treat `./judge` for this surface: run it when in doubt, not only when told to.

**What this does NOT deprecate.** `led`, `judge`, `pickup`, `distance-to-clean`, `attest-tags`,
`audit` are explicitly declared, in the spec's own §1, as the remaining sanctioned non-service
surface — routing them through this service is a reserved v2 question, not something this build
did. If you are an orchestrator session working directly in a world's checkout, keep using the
verbs; this service exists for the panel and any future non-CLI consumer.

**One live gap, named rather than hidden:** the panel-side deprecation marking of its own
direct-psql access (spec §6) is explicitly out of scope for this checkout — it is a separate
autoharn-panel-repo session's item, citing this spec. If you land in that repo, read the spec's
§6 before touching its FastAPI-side SQL.
