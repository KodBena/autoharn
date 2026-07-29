subject: 8e59a2d8
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

New law, not a new verb or refusal: [ADR-0021](../law/adr/0021-witness-construction-discipline.md)
names a failure mode the access-control batch's own review found twice in one day — a witness
(a seen-red fixture leg, a detect artifact, a review reproduction) that passes every procedural
bar (it exists, it runs, it goes red then green in the right order) while certifying nothing,
because its red is red for the wrong reason or its anchor is adjacent prose rather than
behavior. Four rules: observe the claimed property at its own site; convert a negative claim
("X is never reached") into a tripwire whose firing IS the observation, never reuse whatever
fails nearby; anchor on behavior, never a comment or a grep-able string; both polarities,
red first, each for the right reason.

**What a restarting orchestrator doing review would want to know:** when judging a fix's own
witness (yours or a builder's), ask the two questions this ADR gives a name to — "what does
this actually observe?" and "can its red be red for another reason?" — per leg, not just once
per fixture. Enforcement is review-only today (no gate mechanizes this yet; the named
candidate is an extension of `gates/fixture_census.py`). If a witness's red turns out to be a
garbage input dying downstream rather than the named defect, that is not a red — say so rather
than crediting the fixture.
