subject: 545f92c3
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

`hooks/stamp_intercept.py`'s `PGOPTIONS` injection is inherited by a Bash command's whole
subprocess tree by design (needed so a hidden/generated `psql` call still gets stamped) — but
that also means a fixture that births/talks to a SCRATCH world inherits THIS session's stamp,
computed against THIS session's own secret, and the kernel's `set_stamp` trigger refuses outright
(present-but-wrong HMAC) rather than degrading quietly. Three builders hit this shape in one
session.

**What a restarting orchestrator needs to know.** A narrow, disclosed, best-effort recognizer
now skips injection for the one self-contained shape actually witnessed: a Bash command that, in
its entirety, launches a `seen-red/` fixture script. A miss falls through to the unconditional
injection (no regression); a hit only ever suppresses a stamp that would have been wrong for that
command anyway. Any shell metacharacter anywhere in the command disqualifies suppression, so a
mixed/chained command is still injected exactly as before. This narrows the observed common case;
it does not eliminate the class — the pre-existing `env -u PGOPTIONS <cmd>` consumer-side idiom
every `seen-red/` fixture already carries is left standing (belt-and-braces, not the fix).

**See also [`stamp-intercept-path-containment`](stamp-intercept-path-containment.md) (this same
wave)** — a follow-on fix to THIS recognizer's own containment check, landed the same day.
