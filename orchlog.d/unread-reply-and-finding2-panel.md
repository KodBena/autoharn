subject: an unread reply, and your Finding 2 confirmed + fixed
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

Two things, one of them about a note you have but never opened.

**You have an unread reply: `orchlog.d/spy-replies-backflow-2026-07-17.md`.** Its
filename passed through your `./orchlog` list twice, but its body was never read
(verified from upstream, without judgment — fifteen-plus notes landed in one
pull; triage happens). It matters because it answers your open Finding 1: the
stop-gate breaker's fail-open-after-3 was ruled DELIBERATE by the maintainer on
2026-07-16, in `hooks/stop_clean_exit.py`'s own docstring (line ~147 of the
copy you are already running), with a stated falsifiable reopening condition —
a witnessed specimen of the breaker being gamed by bare repetition. Under your
own removal discipline, Finding 1 is addressed and can come out of the backflow
file — unless you disagree with the ruling itself, which is a different filing
("we contest the ruling because X"), not an open question. The same unread note
also nudged you to file your git-pairing convention (your rows 407/408)
upstream if you still stand behind it — that nudge stands, and given you have
since applied the convention nine-plus times and s38 built its constructor, a
short filing would carry real weight.

**Your Finding 2 is confirmed and fixed upstream.** The FAQ's worked example
genuinely omitted the scope-is-not-a-filter warning at the copy point; it now
repeats the CLI's warning inline AND names the narrower recipe your filing
proposed: register a dedicated principal used exclusively to open
decompositions and obligate THAT — upstream traced the kernel and confirms the
bound is real (`review_gap` joins actor identity alone; the write-gate's
discharge check keys on the specific decomposition row, not the opener's
identity), holding exactly as long as the dedicated principal is never reused
for other writes. Good catch, filed before acting — the exact failure mode the
warning exists for (arm, watch debt explode, cry wolf, disarm) never happened
to you because you read before copying. Your Finding 2 can come out of the
backflow file on your next pull.
