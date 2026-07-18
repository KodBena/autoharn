# PROVENANCE

This file records where the `hack-rationalization-detector` skill in this directory came from
and why its body must never be edited here, for anyone touching this scaffold template
(`bootstrap/templates/claude-skills/hack-rationalization-detector/`) or wondering why a
deployment's `.claude/skills/hack-rationalization-detector/` looks the way it does.

This skill was vendored **verbatim** on 2026-07-15 from autoharn's maintainer's own personal,
user-level Claude Code skill, which lived (and still lives) at
`~/.claude/skills/hack-rationalization-detector/` on his machine — a copy scoped to his own
account, not to any one project, and not previously reachable by a scaffolded deployment. The
source copy's own file timestamp at vendor time was: `SKILL.md` last modified 2026-07-06. This
vendoring is autoharn's work item `skill-vendoring-hack-rationalization` (this project's
append-only decision/audit ledger, read via the `./led` command-line tool — see
`.claude/HOOKS.md` in any scaffolded deployment, or `CLAUDE.md` in this repository, for what
that ledger is). Every file under this directory except this one is a byte-for-byte copy of the
source (`diff -r` clean at vendor time): the skill body is not autoharn's to edit — a wanted
change belongs upstream, in the maintainer's personal copy, not here.

`bootstrap/new-project.sh` installs this whole directory into `<dest>/.claude/skills/
hack-rationalization-detector/` at scaffold time, unconditionally — there is no flag to opt a
deployment out of receiving it.

## The precedence fact this vendoring depends on

Claude Code resolves same-named skills by precedence: **enterprise** (an organization-wide skill
set an administrator manages centrally, outside any one user's or project's own files) **>
personal** (`~/.claude/skills/`, one user's own account) **> project** (`.claude/skills/` inside
one repository, this vendored copy's home once scaffolded). A project-level skill is
**shadowed** by anything of the same name at the personal or enterprise level. Concretely: on
the maintainer's own machine, his
personal `~/.claude/skills/hack-rationalization-detector/` — the very copy this one was vendored
from — always wins over the scaffolded project copy, silently, by that platform rule.

**Consequence:** duplication is idempotent, not harmful. There is no drift hazard to warn about
in the sense of "two different behaviors fighting" — whichever copy is *effective* is decided by
a fixed platform resolution rule, not a race, and a project-level copy scaffolded here can never
override a personal one of the same name. What CAN drift is which snapshot in time is effective:
the maintainer's personal copy evolves on his machine independent of this vendored one, so the
two can diverge in content over time even though only one is ever active per Claude Code's own
resolution rule. No mechanism here detects that divergence (none is needed for precedence to
work correctly — it always resolves the same way regardless) — this file records the vendored
copy's own source date above precisely so a future reader can tell, by eye, how stale this copy
might be relative to the maintainer's current personal one, without any tooling promising to
tell them automatically.
