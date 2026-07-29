subject: 5c580ef0,3ca32ca3
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

`kernel/lineage/s70-scope-binding.sql` lands scopes as a first-class, ledgered concept: a new
`principal_scope_bound` kind, a `principal_scopes` derived view, a `scope_disclosure_mode`
vocabulary (`marked` / `hash_stub` / `full`, default `marked`), and the fail-safe default that
makes it additive — a principal with no bound scope holds the OPEN scope, byte-identical to
every world today.

**What a restarting orchestrator needs to know before reaching for this:** s70 (and its
row-level-security sibling s71) rides `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` for the
NEXT `--new-world` scaffold. It is NOT applied to autoharn3 or any other already-born world —
runs are linear, and a live world never gets a retroactive kernel delta. If you `psql` into an
existing deployment's kernel schema looking for `principal_scope_bound`, it will not be there
until a fresh world is born after this delta landed.

**What IS live on main today:** `./autoharn dispatch mint` gained three flags —
`--scope-surface <name>` (repeatable), `--scope-exclude <family>:<value>` (repeatable; family
is one of `kind-class`/`thread`/`work-item-lineage`/`rows`, the closed vocabulary
`tools/dispatch_scope.py` mirrors from the kernel's own CHECK), and `--scope-disclosure-mode
<marked|hash_stub|full>`. Omitting every `--scope-*` flag leaves `mint` byte-identical to
before — no `principal_scope_bound` row is even attempted. Passing one on a pre-s70 world
(i.e. today's autoharn3) will mint the delegate principal and dispatch edge successfully, then
have its scope-bind write REFUSED by the kernel (unknown kind) — `dispatch_scope.bind_scope`
prints a loud stderr warning naming the delegate as holding the OPEN scope, not the requested
one, and tells you not to emit its stamp material until resolved. If you see that warning, the
world you're on predates s70 — this is expected, not a bug to chase.
