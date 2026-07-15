subject: b56b244
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

If you remember the stop gate blocking your session over queue items you had not even
claimed, that is fixed: an unclaimed OPEN work item no longer blocks a stop. Only a CLAIMED
item still needs disposing of before a stop -- either close it, or bequeath it explicitly in
the stop message with `stopping: ...; remains: <slug>`. As a side effect, the fail-open
banner that used to fire on the ordinary, nothing-wrong "planned queue with a few open items"
shape no longer fires there either -- if you were used to seeing that banner routinely, its
absence now is expected, not a sign the check stopped running.
