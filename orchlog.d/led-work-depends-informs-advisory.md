subject: 5f8a15e
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

`led work depends` run without `--type` now prints a stderr advisory: the edge it creates
defaults to `informs`, which is never enforced -- it will not block anything from closing.
If what you actually mean is "X must finish before Y may close", pass `--type blocks-close`
explicitly; do not rely on the default to gate a close.
