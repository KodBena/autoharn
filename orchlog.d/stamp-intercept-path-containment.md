subject: affc9fb6
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

Fixes a real gap in the scratch-fixture recognizer landed by
[`stamp-intercept-scratch-scope`](stamp-intercept-scratch-scope.md) (this same wave): it accepted
`script.startswith("seen-red/")` as containment, so
`python3 seen-red/../not_a_fixture.py` was suppressed even though the traversal resolves OUTSIDE
`seen-red/` — falsifying the module's own documented invariant that suppression can never
withhold a stamp a legitimate own-world write needed.

**What a restarting orchestrator needs to know.** The recognizer now resolves the candidate
script path with `os.path.realpath` against the hook's cwd, resolves `seen-red/` itself the same
way, and requires the script to equal that base or start with it plus a trailing separator — not
a bare textual prefix check — before suppressing. A path that traverses out, or a sibling
directory like `seen-red-evil/x.py`, now falls through to the unconditional injection, the
fail-safe direction this module has documented throughout. If you are writing a NEW `seen-red/`
fixture that launches a script via a relative path containing `..`, expect it to get stamped
(correctly) rather than suppressed — that is this fix, not a regression.
