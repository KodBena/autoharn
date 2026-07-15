subject: 12e2e64
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

`led` now REFUSES a flag placed after the statement text, instead of silently swallowing it
into the statement's own prose (a flag stray in the middle of your recorded statement used to
just become part of the record, unflagged). If `led` refuses your invocation over flag
placement, move every `--flag` before the statement argument, not after it.
