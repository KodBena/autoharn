# Governed files — what the change gate protects

`governed_files.json` is the one place this project chooses which files the ledger
change-gate (`hooks/pretooluse_change_gate.py` in autoharn, wired below) refuses to let
Claude Code edit without a preceding ledger entry.

Format:

```json
{ "patterns": ["*.py"] }
```

Each pattern is matched with Python's `fnmatch` against the path *relative to this project's
root*, and also against the bare filename — so `"*.py"` reaches nested files (fnmatch's `*`
matches `/` too; no `**` needed), and `"config.toml"` matches that one file anywhere. Add or
remove patterns freely; there is no code change required, no allowlist to edit elsewhere, and
no hardcoded file set anywhere in the hook. If this file is missing, unreadable, or malformed,
the gate falls back to the same default it ships with: every `*.py` file, class-keyed — a
project that has not yet configured governance is not silently ungoverned.

Examples:
- `{"patterns": ["*.py", "*.sql"]}` — also govern SQL migrations.
- `{"patterns": ["src/*.py"]}` — govern only the `src/` tree, leave scratch scripts free.
