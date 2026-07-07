# Publishing autoharn — the gates, the mechanism, the timing

Ruled by Fable (session `7be3443d`, 2026-07-06) under maintainer-delegated authority;
executed forensics on the full unpushed range (175 commits, ~5.7M insertions) before
ruling. **Verdict: DO NOT push `main` to origin now.** Not caution-in-general — two
content classes in the range are legitimately unpublishable, one permanently and one
until e15 closes, and both are interleaved through commits whose hashes the audit
trail cross-references.

## The forensic inventory (2026-07-06)

1. **Copyright-restricted PDFs — PERMANENT exclusion.** `experiments/fact-mining/docs/
   {safety-critical-logging-standards,incomplete-evidence-standards}/sources/*.pdf`
   (ISO, IAASB/IESBA handbook, MHRA, ACPO, arXiv). Added in-range by commits whose own
   messages already rule them off GitHub (e857aa4: "local main only; off GitHub for
   copyright"). They stay tracked LOCALLY (they are the BRIEF's evidence base;
   auditability wants them versioned) and never reach a public remote.
2. **e15 blind material — TEMPORAL gate.** The committed session ephemera for the
   Increment-4 builder sessions (`docs/claude-ephemera/session-f91226ce/`,
   `session-55eec152/`) embed the e15 oracle tokens, packet content, and change-order
   text inside their transcripts (verified by grep: `vsr_rw`, `nk4`, the change-order
   sentence). Publishing before the run hands a web-capable subject the blind.
   Publishable the moment e15 closes — it is evidence then. **Standing rule this
   generalizes to: session ephemera containing pre-run design/oracle/packet material
   gate publication until the affected run closes.** (This recurs for every future
   experiment; check before every push.)
3. **Verified clean:** commit identities in-range are placeholder-only
   (`bork you@example.com`); no probe material anywhere in the tree (the `phantom`
   hits are type-theory and buffer-accounting vocabulary); no credentials found
   (pg_hba work happened host-side; `trust` auth means no secrets exist to leak).
4. **The operator repo (`~/w/vdc/1/epistemic-operator`) has NO remote, by design.**
   It is the blind's home (oracles, packets, verbatim change-orders, e16 seed). It
   stays unpublished at least until the runs that its designs govern have closed;
   whether it ever gets a remote is a separate maintainer decision, post-series.

## The mechanism (when the temporal gate opens)

**Never rewrite local `main`.** Consults, witnesses, and ephemera cite harness commit
hashes; a rewrite dangles the audit chain that this project exists to keep sound.
Local `main` is the record of record. Publish via a FILTERED MIRROR instead:

    # after e15 closes; run on a fresh clone, never in the working tree
    git clone ~/w/vdc/1/claude_harness /tmp/autoharn-public && cd /tmp/autoharn-public
    git filter-repo --invert-paths \
      --path experiments/fact-mining/docs/safety-critical-logging-standards/sources \
      --path experiments/fact-mining/docs/incomplete-evidence-standards/sources
    # bank the commit-map (old-hash -> new-hash) back into the local repo as the
    # declared mapping between the record of record and the public view:
    cp .git/filter-repo/commit-map ~/w/vdc/1/claude_harness/docs/publish-commit-map-<date>.txt
    git push --force https://github.com/KodBena/autoharn.git main

The public mirror declares itself a filtered view (add one README line at publish
time naming the two excluded source dirs and pointing at the commit-map). This
satisfies the publish-full-fidelity posture: everything is published except the two
declared classes, and the mapping from public hashes to record-of-record hashes is
itself banked and auditable.

## Future-proofing (small, do in any increment)

A versioned pre-push guard (`tools/hooks/pre-push`) that refuses any push to origin
whose range adds `*.pdf` under a `sources/` dir or touches `docs/claude-ephemera/`
for a session whose run has not closed (maintain a small closed-runs list in the
hook's config). Mechanizes rule 2's "check before every push" so the check cannot be
forgotten once no one remembers this file.

## ADDENDUM (2026-07-07 ~01:10) — EMERGENCY PUBLIC RELEASE, maintainer-ruled

The maintainer ruled publication ("I *want* it published"), superseding the hold above;
the emergency is machine-loss risk at the Fable-withdrawal boundary. Gates honored by
REDACTION IN THE MIRROR, not by holding back:
1. The two copyright `sources/` dirs: excluded by path (as planned above).
2. One undisclosed-instrumentation memory reference (appears in session-transcript
   ephemera via the loaded memory index, and appeared in the harness DB dump): redacted
   by content-replace in the public mirror (`[REDACTED-MEM]`); the dump in the operator
   repo was redacted at source before its commit. Local main remains full-fidelity.
3. e15 blind material: gate OPEN (e15 closed 2026-07-07 00:20).
4. e16-design-SEED becomes public with the operator repo: PRE-REGISTERED RESIDUAL —
   e16 subjects must be run without web-capable tools (one line in the e16 arming
   checklist), same class as the accepted label residuals.
RECIPE used (rerunnable after future commits): fresh clone → git-filter-repo
--invert-paths the two sources/ dirs + --replace-text redact-rules → push --force to
origin main; bank .git/filter-repo/commit-map into docs/ locally. Operator repo:
pushed as-is (swept clean) to a new public repo. DB dumps + shipped artifact live in
the operator repo (db-dumps/, harness/e15-build/artifact-snapshot/).
