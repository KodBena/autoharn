subject: f8af7d7e
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

`GET /d/{deployment}/attestation` used to answer `NoBankedArtifact` for `verify-chain`/`doctor`
on any checkout, always — only `judge` ever banked. As of this delta, `libexec/autoharn/
verify-chain` and `libexec/autoharn/doctor` themselves bank each ORDINARY run's result under
`engine/docs/ledger-marriage/derivations/{verify-chain,doctor}/<ts>_<hash>/result.json` — the
same storage home and subdirectory convention `judge` already used, added at the operator-verb
wrapper layer (their `bootstrap/templates/*.tmpl` internals are untouched). `--head` is
deliberately excluded (a different artifact, the operator's own GPG ceremony). A banking write
failure never changes the verb's own exit code.

**What a restarting orchestrator needs to know:** the attestation route now genuinely serves all
three instruments' last-known result once you've run `./autoharn verify-chain`/`./autoharn
doctor`/`./autoharn judge` at least once — for THIS repo's own operator verbs (not the bare
library CLIs), banking IS the ordinary run, not an opportunistic extra. A checkout that has
never run one of the three still resolves that instrument's field to `NoBankedArtifact`,
honestly, with `would_produce` now naming a command that genuinely populates the route (verified
both before-any-run and after, live). The route never runs any instrument itself — it only reads
what a prior `./autoharn <instrument>` invocation already wrote to disk; the two-trust-roots
posture (`serving/README.md`) is unchanged.

WITNESSED live on this checkout: `curl http://127.0.0.1:8433/d/autoharn3/attestation` after a
fresh `service restart` returned banked `verify_chain`/`judge`/`doctor` fields together, all
three genuinely populated.
